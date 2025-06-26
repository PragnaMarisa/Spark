# Checkpointing in Apache Spark

## What is Checkpointing?

**Checkpointing** is a fault tolerance mechanism that saves RDDs/DataFrames to **reliable storage** (like HDFS) to **truncate long lineage chains** and prevent expensive recomputation in case of failures.

## Purpose and Benefits

### Why Checkpoint?
- **Truncate lineage chains**: Break long dependency chains that can become expensive to recompute
- **Fault tolerance**: Faster recovery by reading from disk instead of recomputing
- **Memory efficiency**: Reduce memory pressure from storing long lineage information
- **Performance**: Avoid exponential recomputation in iterative algorithms

### When to Use Checkpointing
- **Long-running jobs** with complex transformations
- **Iterative algorithms** (Machine Learning, GraphX)
- **Structured Streaming** applications
- **Wide dependency operations** that create shuffle boundaries
- When **lineage chain becomes too long** (>10 stages)

---

## Types of Checkpointing

### 1. RDD Checkpointing
```scala
// Set checkpoint directory (must be fault-tolerant storage)
sc.setCheckpointDir("hdfs://cluster/checkpoints")

val data = sc.textFile("large_dataset.txt")
val processed = data
  .map(parseRecord)
  .filter(_.isValid)
  .map(transform)
  .cache()  // Cache before checkpoint for efficiency

// Mark for checkpointing
processed.checkpoint()

// Trigger action to execute checkpoint
processed.count()  // This will save data to checkpoint directory

// Lineage is now truncated - future operations start from checkpoint
val final = processed.map(finalTransform).collect()
```

### 2. DataFrame Checkpointing
```scala
import spark.implicits._

// Set checkpoint directory
spark.sparkContext.setCheckpointDir("hdfs://cluster/checkpoints")

val df = spark.read.parquet("input/")
val processed = df
  .filter($"status" === "active")
  .groupBy($"category")
  .agg(sum($"amount"))
  .cache()

// Checkpoint DataFrame
processed.checkpoint()
processed.count()  // Trigger checkpoint

// Use checkpointed DataFrame
val result = processed.join(otherDF, "category")
```

---

## Checkpointing in Streaming

### Structured Streaming Checkpointing
```scala
val streamingQuery = spark
  .readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("subscribe", "input-topic")
  .load()
  .selectExpr("CAST(value AS STRING)")
  .writeStream
  .format("console")
  .option("checkpointLocation", "hdfs://cluster/streaming-checkpoints")  // Essential for streaming
  .start()

streamingQuery.awaitTermination()
```

### What Gets Checkpointed in Streaming?
- **Offset information**: Track progress in input sources
- **State information**: For stateful operations (aggregations, joins)
- **Configuration**: Query configuration and metadata
- **Lineage**: Transformation logic for recovery

---

## Checkpointing vs Caching

| Feature | **Caching** | **Checkpointing** |
|---------|-------------|-------------------|
| **Storage** | Memory/Disk (local) | Reliable storage (HDFS) |
| **Purpose** | Performance optimization | Fault tolerance |
| **Lineage** | Preserves lineage | **Truncates lineage** |
| **Persistence** | Lost on application restart | **Survives application restart** |
| **Cost** | Low | Higher (network I/O) |
| **Recovery** | Recompute from lineage | **Read from disk** |

### Combined Usage Pattern
```scala
val expensiveData = rawData
  .map(expensiveTransformation)
  .filter(complexPredicate)
  .cache()  // For immediate reuse

expensiveData.checkpoint()  // For fault tolerance
expensiveData.count()  // Trigger both caching and checkpointing

// Now data is both cached AND checkpointed
val result1 = expensiveData.map(transform1)  // Uses cache
val result2 = expensiveData.map(transform2)  // Uses cache

// If cache is lost, data is read from checkpoint (not recomputed)
```

---

## Best Practices

### 1. Choose Appropriate Checkpoint Location
```scala
// GOOD: Reliable, distributed storage
sc.setCheckpointDir("hdfs://cluster/checkpoints")
sc.setCheckpointDir("s3a://bucket/checkpoints")

// BAD: Local filesystem (not fault-tolerant)
sc.setCheckpointDir("file:///tmp/checkpoints")
```

### 2. Cache Before Checkpointing
```scala
// RECOMMENDED: Cache first, then checkpoint
val processed = data.map(expensiveOperation).cache()
processed.checkpoint()
processed.count()  // Triggers both caching and checkpointing

// INEFFICIENT: Will compute twice
val processed = data.map(expensiveOperation)
processed.checkpoint()
processed.count()  // Computes and saves to checkpoint
processed.collect()  // Computes again from scratch
```

### 3. Strategic Checkpoint Placement
```scala
// Checkpoint after expensive operations but before further processing
val stage1 = rawData.map(expensiveETL).cache()
stage1.checkpoint()
stage1.count()

val stage2 = stage1.join(lookupData).groupBy("key").agg(sum("value"))
// Don't checkpoint stage2 if it's simple and final
```

---

## Iterative Algorithm Example

### Machine Learning with Checkpointing
```scala
sc.setCheckpointDir("hdfs://cluster/ml-checkpoints")

var data = initialData.cache()
data.checkpoint()
data.count()

for (iteration <- 1 to 100) {
  // Expensive iterative computation
  data = data.map(mlStep).cache()
  
  // Checkpoint every 10 iterations to control lineage growth
  if (iteration % 10 == 0) {
    data.checkpoint()
    data.count()
    println(s"Checkpointed at iteration $iteration")
  }
}

val finalModel = data.collect()
```

### GraphX with Checkpointing
```scala
import org.apache.spark.graphx._

sc.setCheckpointDir("hdfs://cluster/graph-checkpoints")

var graph = GraphLoader.edgeListFile(sc, "graph.txt")
graph.cache()
graph.vertices.checkpoint()
graph.edges.checkpoint()

for (i <- 1 to 20) {
  graph = graph.pregel(initialMsg, maxIterations = 1)(
    vprog = vertexProgram,
    sendMsg = sendMessage,
    mergeMsg = mergeMessages
  )
  
  // Checkpoint every 5 iterations
  if (i % 5 == 0) {
    graph.cache()
    graph.vertices.checkpoint()
    graph.edges.checkpoint()
    graph.vertices.count()  // Trigger checkpoint
  }
}
```

---

## Monitoring and Debugging

### Check Lineage Length
```scala
// Monitor RDD lineage depth
def printLineage(rdd: RDD[_], depth: Int = 0): Unit = {
  println("  " * depth + rdd.toString())
  rdd.dependencies.foreach(dep => printLineage(dep.rdd, depth + 1))
}

printLineage(myRDD)
```

### Checkpoint Status
```scala
// Check if RDD is checkpointed
if (rdd.isCheckpointed) {
  println(s"RDD is checkpointed at: ${rdd.getCheckpointFile}")
} else {
  println("RDD is not checkpointed")
}
```

### Streaming Checkpoint Recovery
```scala
// Function to create or recover streaming query
def createOrRecoverQuery(checkpointPath: String): StreamingQuery = {
  spark
    .readStream
    .format("kafka")
    .load()
    .writeStream
    .format("console")
    .option("checkpointLocation", checkpointPath)
    .start()
}

// This will recover from checkpoint if exists, otherwise start fresh
val query = createOrRecoverQuery("hdfs://cluster/streaming-checkpoints")
```

---

## Common Pitfalls

### 1. Forgetting to Trigger Action
```scala
// WRONG: Checkpoint not actually saved
val data = rdd.map(transform)
data.checkpoint()  // Just marks for checkpointing
// No action called - checkpoint never happens!

// CORRECT: Trigger action to save checkpoint
val data = rdd.map(transform)
data.checkpoint()
data.count()  // Now checkpoint is actually saved
```

### 2. Unreliable Checkpoint Directory
```scala
// DANGEROUS: Local filesystem not fault-tolerant
sc.setCheckpointDir("/tmp/checkpoints")

// SAFE: Distributed, fault-tolerant storage
sc.setCheckpointDir("hdfs://cluster/checkpoints")
```

### 3. Over-checkpointing
```scala
// INEFFICIENT: Too frequent checkpointing
for (i <- 1 to 100) {
  data = data.map(step)
  data.checkpoint()  // Every iteration - too expensive!
  data.count()
}

// BETTER: Checkpoint periodically
for (i <- 1 to 100) {
  data = data.map(step)
  if (i % 10 == 0) {  // Every 10 iterations
    data.checkpoint()
    data.count()
  }
}
```

---

## Performance Considerations

### Checkpoint Overhead
- **I/O cost**: Writing to reliable storage takes time
- **Serialization**: Objects must be serialized to disk
- **Network**: May involve network transfers to distributed storage

### Optimization Tips
1. **Batch checkpoints**: Don't checkpoint every iteration
2. **Use appropriate storage**: Fast, reliable storage systems
3. **Combine with caching**: Cache frequently accessed checkpointed data
4. **Clean up**: Remove old checkpoints when no longer needed

```scala
// Clean up old checkpoints periodically
import org.apache.hadoop.fs.{FileSystem, Path}

val fs = FileSystem.get(sc.hadoopConfiguration)
val oldCheckpoints = fs.listStatus(new Path("hdfs://cluster/checkpoints"))
  .filter(_.getMo
