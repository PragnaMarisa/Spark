# Spark Memory Management

## Spark Memory Model

Spark divides executor memory into several regions for different purposes. Understanding this is crucial for performance tuning.

## Memory Regions

### 1. Reserved Memory (300 MB)
- **Fixed size**: Always 300 MB per executor
- **Purpose**: System reserved memory for Spark internal objects
- **Cannot be configured**

### 2. User Memory
- **Formula**: `(Executor Memory - Reserved Memory) × (1 - spark.memory.fraction)`
- **Default**: ~40% of available memory (when fraction = 0.6)
- **Purpose**: User data structures, UDFs, and custom objects
- **Not managed by Spark**

### 3. Spark Memory (Unified Memory)
- **Formula**: `(Executor Memory - Reserved Memory) × spark.memory.fraction`
- **Default**: ~60% of available memory
- **Managed by Spark** and divided into two parts:

#### 3a. Storage Memory
- **Purpose**: Caching RDDs, DataFrames, and broadcast variables
- **Operations**: `cache()`, `persist()`, broadcast joins
- **Eviction**: LRU (Least Recently Used) when memory pressure

#### 3b. Execution Memory  
- **Purpose**: Shuffle operations, joins, sorts, aggregations
- **Operations**: Wide transformations requiring shuffle
- **Temporary**: Released after task completion

## Unified Memory Management

### Dynamic Allocation
- **Storage and Execution memory can borrow from each other**
- **Execution can evict Storage** (but not vice versa)
- **Storage cannot evict Execution** (would cause task failure)

### Memory Borrowing Rules
```
If Execution needs memory:
├── Use its own pool first
├── If insufficient, borrow from Storage pool  
└── Evict cached data if necessary (LRU)

If Storage needs memory:
├── Use its own pool first
├── If insufficient, borrow from Execution pool
└── Wait if Execution pool is busy (no eviction)
```

## Key Configuration Parameters

### Basic Memory Settings
```conf
# Total executor memory
spark.executor.memory = 4g

# Memory fraction for Spark (vs User memory)  
spark.memory.fraction = 0.6

# Storage fraction within Spark memory
spark.memory.storageFraction = 0.5

# Off-heap memory
spark.memory.offHeap.enabled = true
spark.memory.offHeap.size = 2g
```

### Advanced Settings
```conf
# Memory overhead for JVM processes
spark.executor.memoryOverhead = 1g

# PySpark memory (Python worker processes)
spark.executor.pyspark.memory = 2g
```

## Memory Calculation Example

**Given**: `spark.executor.memory = 8g`

```
Total Executor Memory: 8 GB
├── Reserved Memory: 300 MB (fixed)
├── Available Memory: 7.7 GB
    ├── User Memory: 7.7GB × 0.4 = 3.08 GB
    └── Spark Memory: 7.7GB × 0.6 = 4.62 GB
        ├── Storage Memory: 4.62GB × 0.5 = 2.31 GB  
        └── Execution Memory: 4.62GB × 0.5 = 2.31 GB
```

## Storage Memory Deep Dive

### What Gets Stored
- **Cached RDDs/DataFrames**: Via `cache()` or `persist()`
- **Broadcast Variables**: Small datasets broadcast to all executors
- **Unroll Memory**: Temporary space for unrolling blocks

### Storage Levels Impact
```scala
// Different storage levels use memory differently
df.persist(StorageLevel.MEMORY_ONLY)          // Uses Storage memory
df.persist(StorageLevel.MEMORY_AND_DISK)      // Uses Storage + disk spillover  
df.persist(StorageLevel.MEMORY_ONLY_SER)      // Uses less Storage (serialized)
df.persist(StorageLevel.DISK_ONLY)            // No Storage memory used
```

### Eviction Policy
- **LRU (Least Recently Used)**
- Cached data evicted when new cache requests need space
- **Important**: Evicted data may need recomputation!

## Execution Memory Deep Dive

### What Uses Execution Memory
- **Shuffle operations**: `groupByKey()`, `reduceByKey()`, `join()`
- **Sort operations**: `sortBy()`, `orderBy()`
- **Aggregations**: `groupBy().agg()`
- **Window functions**: `window()`, `rank()`

### Memory Pressure Handling
```scala
// If execution memory insufficient:
// 1. Try to borrow from Storage
// 2. Spill to disk if necessary
// 3. May cause OOM if spillover fails
```

## Off-Heap Memory

### Benefits
- **No GC pressure**: Avoids Java garbage collection
- **Better memory utilization**: More predictable memory usage
- **Reduced serialization**: Direct binary storage

### Configuration
```conf
spark.memory.offHeap.enabled = true
spark.memory.offHeap.size = 4g
```

### Use Cases
- **Large cached datasets** that cause GC issues
- **Workloads with high memory pressure**
- **Long-running applications**

## Memory Monitoring

### Spark UI - Executors Tab
- **Storage Memory Used**: How much cache memory is used
- **Memory Fraction**: Percentage of total memory used
- **Max Memory**: Total memory available for storage

### Spark UI - Storage Tab  
- **Cached RDDs/DataFrames**: Size and storage level
- **Fraction Cached**: How much of dataset is in memory

### Key Metrics to Watch
```bash
# Memory utilization
Storage Memory Used / Total Storage Memory

# Cache hit ratio  
Blocks in Memory / Total Blocks

# GC overhead
GC Time / Total Task Time
```

## Common Memory Issues

### 1. Out of Memory (OOM)
```scala
// Problem: Insufficient execution memory
val result = largeDF.groupBy("key").agg(sum("value"))

// Solutions:
// Increase executor memory
spark.conf.set("spark.executor.memory", "8g")

// Increase partitions to reduce per-task memory
val result = largeDF.repartition(200).groupBy("key").agg(sum("value"))

// Use more efficient operations  
val result = largeDF.reduceByKey(_ + _)  // Instead of groupByKey
```

### 2. Excessive GC
```scala
// Problem: Too much cached data causing GC pressure
df.cache()  // Large dataset cached

// Solutions:
// Use serialized storage
df.persist(StorageLevel.MEMORY_ONLY_SER)

// Enable off-heap storage
spark.conf.set("spark.memory.offHeap.enabled", "true")

// Cache selectively
df.filter(importantCondition).cache()  // Cache only needed subset
```

### 3. Memory Fragmentation
```scala
// Problem: Many small cached objects
smallDF1.cache()
smallDF2.cache() 
// ... many small caches

// Solution: Combine related data
val combinedDF = smallDF1.union(smallDF2).cache()
```

## Best Practices

### Memory Sizing
```conf
# General rule: Total memory = Executor memory + Overhead
# Overhead typically 10-15% of executor memory
spark.executor.memory = 7g
spark.executor.memoryOverhead = 1g
```

### Caching Strategy
```scala
// Cache strategically
val expensiveDF = rawData.join(lookup).filter(complexCondition)
expensiveDF.cache()  // Only cache if used multiple times

// Use appropriate storage level
df.persist(StorageLevel.MEMORY_AND_DISK_SER)  // Good balance

// Unpersist when done
expensiveDF.unpersist()
```

### Memory Tuning
```conf
# For cache-heavy workloads
spark.memory.fraction = 0.8
spark.memory.storageFraction = 0.7

# For computation-heavy workloads  
spark.memory.fraction = 0.6
spark.memory.storageFraction = 0.3
```

## Memory Anti-Patterns

### ❌ Don't Do This
```scala
// Caching everything
df1.cache()
df2.cache()
df3.cache()  // May cause memory pressure

// Using collect() on large datasets
val allData = largeDF.collect()  // Brings everything to driver

// Inefficient operations
largeDF.groupByKey().mapValues(_.sum)  // Use reduceByKey instead
```

### ✅ Do This Instead
```scala
// Strategic caching
val frequentlyUsed = df.filter(condition).cache()

// Process data in chunks
largeDF.foreachPartition { partition =>
  // Process each partition separately
}

// Efficient aggregations
largeDF.reduceByKey(_ + _)  // More memory efficient
```
