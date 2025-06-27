# Spark Performance Tuning Guide

## Overview

Performance tuning in Apache Spark involves optimizing multiple layers: application design, resource allocation, data organization, and configuration parameters. This guide covers practical strategies and configurations for maximizing Spark performance.

## 1. Application-Level Optimizations

### Choose the Right Operations

#### Use Efficient Transformations
```scala
// ❌ Inefficient: Creates large intermediate collections
val result = data.groupByKey().mapValues(_.sum)

// ✅ Efficient: Reduces data before grouping
val result = data.reduceByKey(_ + _)
```

#### Minimize Shuffles
```scala
// ❌ Multiple shuffles
val df1 = data.groupBy("key1").sum()
val df2 = df1.groupBy("key2").sum()

// ✅ Single shuffle with multiple aggregations
val result = data.groupBy("key1", "key2").agg(
  sum("value1"), 
  avg("value2")
)
```

#### Use Broadcast for Small Tables
```scala
// ❌ Large shuffle for small lookup table
val joined = largeDF.join(smallDF, "key")

// ✅ Broadcast join eliminates shuffle
val joined = largeDF.join(broadcast(smallDF), "key")
```

### Optimize Data Access Patterns

#### Predicate Pushdown
```scala
// ✅ Filter early to reduce data processing
val filtered = spark.read.parquet("large_dataset")
  .filter($"date" >= "2024-01-01")  // Pushed down to file level
  .filter($"status" === "active")   // Further filtering
```

#### Column Pruning
```scala
// ❌ Reading unnecessary columns
val result = spark.read.parquet("wide_table").groupBy("key").count()

// ✅ Select only needed columns  
val result = spark.read.parquet("wide_table")
  .select("key")
  .groupBy("key").count()
```

## 2. Data Organization Optimizations

### File Formats

#### Choose Efficient Formats
| Format | Use Case | Pros | Cons |
|--------|----------|------|------|
| **Parquet** | Analytics, columnar access | Compression, predicate pushdown | Write overhead |
| **Delta Lake** | ACID operations, updates | Versioning, ACID, schema evolution | Additional complexity |
| **ORC** | Hive integration | Good compression | Less Spark-optimized |
| **JSON** | Semi-structured data | Flexible schema | Poor performance |
| **CSV** | Legacy/simple data | Human readable | No schema, slow parsing |

#### Optimal File Sizes
```scala
// ❌ Many small files (< 100MB each)
df.write.mode("overwrite").parquet("output/")

// ✅ Fewer, larger files (100MB - 1GB each)
df.coalesce(numPartitions).write.mode("overwrite").parquet("output/")
```

### Partitioning Strategies

#### Partition by Frequently Filtered Columns
```scala
// ✅ Partition by date for time-series queries
df.write
  .partitionBy("year", "month")
  .mode("overwrite")
  .parquet("partitioned_data/")

// Query benefits from partition pruning
spark.read.parquet("partitioned_data/")
  .filter($"year" === 2024 && $"month" === 6)  // Only reads relevant partitions
```

#### Avoid Over-Partitioning
```scala
// ❌ Too many partitions (small files)
df.write.partitionBy("user_id").parquet("output/")  // Millions of users

// ✅ Reasonable partitioning  
df.write.partitionBy("region", "date").parquet("output/")  // Hundreds of partitions
```

### Bucketing for Joins
```scala
// ✅ Bucket tables that are frequently joined
df1.write
  .bucketBy(10, "user_id")
  .saveAsTable("user_events")

df2.write  
  .bucketBy(10, "user_id")
  .saveAsTable("user_profiles")

// Join benefits from pre-bucketing (no shuffle)
val joined = spark.table("user_events")
  .join(spark.table("user_profiles"), "user_id")
```

## 3. Resource Configuration Tuning

### Executor Configuration

#### Right-Size Executors
```conf
# ❌ Too large executors (GC issues)
spark.executor.memory = 32g
spark.executor.cores = 16

# ✅ Balanced executors  
spark.executor.memory = 4g
spark.executor.cores = 3
spark.executor.instances = 20
```

#### Memory Distribution
```conf
# For compute-heavy workloads
spark.memory.fraction = 0.6
spark.memory.storageFraction = 0.3

# For cache-heavy workloads
spark.memory.fraction = 0.8  
spark.memory.storageFraction = 0.7
```

### Parallelism Tuning

#### Set Appropriate Partition Count
```scala
// Rule of thumb: 2-3x number of CPU cores in cluster
val idealPartitions = totalCores * 2

// For input data
spark.conf.set("spark.sql.files.maxPartitionBytes", "128MB")

// For shuffles
spark.conf.set("spark.sql.shuffle.partitions", idealPartitions.toString)
```

#### Dynamic Partition Count
```conf
# Enable adaptive query execution
spark.sql.adaptive.enabled = true
spark.sql.adaptive.coalescePartitions.enabled = true
spark.sql.adaptive.coalescePartitions.initialPartitionNum = 1000
spark.sql.adaptive.coalescePartitions.minPartitionSize = 1MB
```

## 4. Caching and Persistence Strategy

### When to Cache
```scala
// ✅ Cache datasets used multiple times
val expensiveDF = rawData
  .join(lookup)
  .filter(complexCondition)
  .groupBy("key").agg(sum("value"))

expensiveDF.cache()  // Used in multiple downstream operations

val result1 = expensiveDF.filter($"value" > 100)
val result2 = expensiveDF.filter($"value" <= 100)

// Don't forget to unpersist
expensiveDF.unpersist()
```

### Choose Right Storage Level
```scala
// For datasets that fit in memory
df.persist(StorageLevel.MEMORY_ONLY)

// For large datasets with serialization
df.persist(StorageLevel.MEMORY_ONLY_SER)

// For datasets larger than memory
df.persist(StorageLevel.MEMORY_AND_DISK_SER)

// For very large datasets
df.persist(StorageLevel.DISK_ONLY)
```

### Cache Granularity
```scala
// ❌ Cache too early (before filtering)
val cached = rawData.cache()
val filtered = cached.filter(complexCondition)

// ✅ Cache after expensive operations
val processed = rawData.join(lookup).filter
