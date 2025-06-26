# Partitions in Apache Spark

## What are Partitions?
**Partitions** are logical chunks of data in distributed datasets (RDD, DataFrame, Dataset). Each partition is processed **independently** by executor tasks, enabling **parallelism** in Spark processing.

## Example
Dataset of 1000 records split into 4 partitions:
- **Partition 1**: Records 1-250
- **Partition 2**: Records 251-500  
- **Partition 3**: Records 501-750
- **Partition 4**: Records 751-1000

## Importance of Partitions

| Benefit | Description |
|---------|-------------|
| 🚀 **Parallelism** | Each partition processed in parallel by separate executor tasks |
| 🔁 **Fault Tolerance** | Each partition's transformation lineage tracked for recovery |
| ⚖️ **Performance** | Right partitioning strategy reduces shuffles and speeds up operations |
| 💾 **Memory Management** | Partitions fit in executor memory independently |

## How Partitions are Created

### From Files
```scala
// HDFS files split by block size (default 128 MB)
val rdd = sc.textFile("hdfs://data/large_file.txt")
// If file is 1 GB, creates ~8 partitions
```

### From Collections
```scala
// Explicitly specify partition count
val rdd = sc.parallelize(1 to 1000, numPartitions = 4)
```

### From Transformations
```scala
// Inherit partitions from parent RDD
val filtered = rdd.filter(x => x > 100)  // Same partition count as rdd
```

## Partition Operations

### repartition(n)
- Can **increase or decrease** partition count
- Requires **full shuffle** (expensive)
- Results in **even distribution** of data

```scala
val morePartitions = df.repartition(10)   // Increase partitions
val fewerPartitions = df.repartition(2)   // Decrease partitions
```

### coalesce(n)
- Used to **reduce partitions only**
- **No shuffle** required (more efficient)
- May result in **uneven partition sizes**
- **No data loss** - just merges adjacent partitions

```scala
val reducedPartitions = df.coalesce(2)    // Only reduces, no shuffle
```

### When to Use Each
| Use Case | Operation | Reason |
|----------|-----------|---------|
| Reduce partitions after filtering | `coalesce()` | More efficient, no shuffle |
| Increase partitions for parallelism | `repartition()` | Only option to increase |
| Even distribution needed | `repartition()` | Guarantees balanced partitions |
| Quick partition reduction | `coalesce()` | Faster, less resource intensive |

## Optimal Partitioning

### Guidelines
- **Too few partitions**: Underutilized cores, less parallelism
- **Too many partitions**: Scheduling overhead, small tasks
- **Rule of thumb**: 2-3 partitions per CPU core in your cluster

### Checking Partition Information
```scala
// Check number of partitions
val numPartitions = rdd.getNumPartitions
println(s"Number of partitions: $numPartitions")

// Check partition sizes
rdd.mapPartitions(iter => Iterator(iter.size)).collect()

// Partition-wise debugging
rdd.mapPartitionsWithIndex { (index, iter) =>
  Iterator(s"Partition $index has ${iter.size} elements")
}.collect()
```

## Performance Considerations

### File Reading
```scala
// Large files automatically split into partitions
val largeFile = spark.read.text("hdfs://large_dataset.txt")
// Spark creates partitions based on HDFS block size
```

### Joins and Shuffles
```scala
// Both RDDs should have compatible partitioning
val rdd1 = data1.repartition(4)
val rdd2 = data2.repartition(4)
val joined = rdd1.join(rdd2)  // More efficient with same partition count
```

### Output Operations
```scala
// Control output file count
df.coalesce(1)              // Single output file
  .write
  .mode("overwrite")
  .csv("output/path")

df.repartition(10)          // 10 output files
  .write
  .parquet("output/path")
```

## Adaptive Query Execution (AQE)
When enabled with `spark.sql.adaptive.enabled = true`:
- Can dynamically **merge small partitions** at runtime
- Optimizes **skewed joins**
- Does **not increase** partition count automatically
- Only works with DataFrames/Datasets, not RDDs

## Best Practices
1. **Monitor partition sizes** - aim for 100MB-1GB per partition
2. **Use `coalesce()` over `repartition()`** when reducing partitions
3. **Partition before expensive operations** like joins
4. **Consider data locality** when partitioning
5. **Cache partitioned data** if used multiple times
6. **Avoid too many small partitions** - causes overhead

## Common Partitioning Scenarios

### After Filtering
```scala
val filtered = largeRDD.filter(expensiveCondition)
val optimized = filtered.coalesce(4)  // Reduce empty partitions
```

### Before Joins
```scala
val partitioned1 = rdd1.repartition(8)
val partitioned2 = rdd2.repartition(8)
val result = partitioned1.join(partitioned2)  // Efficient join
```

### For Output Control
```scala
// Single output file
df.coalesce(1).write.json("single_file_output/")

// Multiple output files for parallel processing
df.repartition(20).write.parquet("parallel_output/")
```
