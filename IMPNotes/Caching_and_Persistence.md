# Caching and Persistence in Spark

## Overview
**Caching** and **Persistence** are optimization techniques in Spark that store frequently accessed data in memory or disk to avoid recomputation.

## cache() vs persist()

| Method | Default Storage Level | Customizable? | Use Case |
|--------|----------------------|---------------|----------|
| `cache()` | MEMORY_ONLY | ❌ No | Simple caching needs |
| `persist()` | User-defined | ✅ Yes | Custom storage requirements |

### Basic Usage
```scala
// Using cache()
val df = spark.read.parquet("data.parquet")
df.cache()  // Stores in memory only

// Using persist()
import org.apache.spark.storage.StorageLevel
df.persist(StorageLevel.MEMORY_AND_DISK)  // Custom storage level
```

---

## Storage Levels

### Available Storage Levels

| Storage Level | Memory | Disk | Serialized | Replicated | Use Case |
|---------------|--------|------|------------|------------|----------|
| `MEMORY_ONLY` | ✅ | ❌ | ❌ | ❌ | **Fastest access**, sufficient memory |
| `MEMORY_ONLY_SER` | ✅ | ❌ | ✅ | ❌ | **Save memory**, slight CPU overhead |
| `MEMORY_AND_DISK` | ✅ | ✅ | ❌ | ❌ | **Balanced approach**, fallback to disk |
| `MEMORY_AND_DISK_SER` | ✅ | ✅ | ✅ | ❌ | **Memory efficient** with disk fallback |
| `DISK_ONLY` | ❌ | ✅ | ❌ | ❌ | **Memory constrained** environments |
| `MEMORY_ONLY_2` | ✅ | ❌ | ❌ | ✅ | **High availability**, 2x memory usage |
| `MEMORY_AND_DISK_2` | ✅ | ✅ | ❌ | ✅ | **Fault tolerant** with replication |

### Choosing the Right Storage Level

#### MEMORY_ONLY
- **Best for**: Small datasets that fit in memory
- **Pros**: Fastest access time
- **Cons**: Data lost if insufficient memory

#### MEMORY_AND_DISK
- **Best for**: Large datasets with frequent access
- **Pros**: Reliable fallback to disk
- **Cons**: Slower disk access when memory is full

#### MEMORY_ONLY_SER
- **Best for**: Large datasets with memory constraints
- **Pros**: Saves memory through serialization
- **Cons**: CPU overhead for serialization/deserialization

---

## When to Use Caching

### Good Candidates for Caching
- **Iterative algorithms**: ML training, graph algorithms
- **Multiple actions**: Same dataset used for multiple operations
- **Expensive computations**: Complex transformations
- **Interactive analysis**: Jupyter notebooks, data exploration

### Example: Iterative Algorithm
```scala
val data = spark.read.parquet("training_data.parquet")
  .filter($"label".isNotNull)
  .cache()  // Cache expensive preprocessing

// Multiple iterations use the same data
for (i <- 1 to 10) {
  val model = trainModel(data, iteration = i)
  val accuracy = evaluate(model, data)
  println(s"Iteration $i: Accuracy = $accuracy")
}

data.unpersist()  // Clean up when done
```

### Example: Multiple Actions
```scala
val processedData = rawData
  .filter($"status" === "active")
  .join(lookupTable, "id")
  .cache()  // Cache before multiple actions

// Multiple actions on same data
val count = processedData.count()
val summary = processedData.describe()
processedData.write.parquet("output/")

processedData.unpersist()
```

---

## Best Practices

### Memory Management
```scala
// Always unpersist when done
df.cache()
// ... use df multiple times
df.unpersist()  // Free memory for other operations
```

### Monitoring Cache Usage
```scala
// Check if RDD is cached
println(s"Is cached: ${df.rdd.getStorageLevel != StorageLevel.NONE}")

// Monitor cache usage in Spark UI
// Go to Storage tab to see cached datasets
```

### Cache Partitioned Data
```scala
// Cache after partitioning for better performance
val partitionedData = data
  .repartition($"date")
  .cache()
```

---

## Common Patterns

### ETL Pipeline Caching
```scala
val cleaned = rawData
  .filter($"quality_score" > 0.8)
  .dropDuplicates()
  .cache()  // Cache clean data

// Multiple outputs from same clean data
cleaned.write.parquet("clean/")
cleaned.groupBy("category").count().write.parquet("summary/")
cleaned.sample(0.1).write.parquet("sample/")

cleaned.unpersist()
```

### ML Pipeline Caching
```scala
val features = data
  .select("features", "label")
  .cache()  // Cache feature vectors

// Use same features for multiple models
val model1 = new LogisticRegression().fit(features)
val model2 = new RandomForestClassifier().fit(features)
val model3 = new GBTClassifier().fit(features)

features.unpersist()
```

---

## Performance Considerations

### Cache Efficiency
- **Cache early**: After expensive transformations
- **Cache selectively**: Only frequently accessed data
- **Monitor memory**: Use Spark UI to track cache usage
- **Unpersist promptly**: Free memory when no longer needed

### Serialization Overhead
```scala
// Kryo serialization for better performance
spark.conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

// Use serialized storage for large datasets
df.persist(StorageLevel.MEMORY_ONLY_SER)
```

### Memory Pressure Handling
```scala
// Spark automatically evicts LRU cached data
// Monitor and adjust cache levels based on memory pressure

// Check memory usage
spark.catalog.listCachedTables()  // For cached tables
```

---

## Troubleshooting

### Common Issues
1. **OutOfMemoryError**: Use `MEMORY_AND_DISK` instead of `MEMORY_ONLY`
2. **Slow performance**: Check if data is actually cached
3. **Memory leaks**: Ensure `unpersist()` is called

### Debugging Cache Issues
```scala
// Check storage level
println(df.rdd.getStorageLevel)

// Force caching with an action
df.cache()
df.count()  // Triggers caching

// Monitor in Spark UI Storage tab
```
