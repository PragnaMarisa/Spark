# Spark Stages and Tasks

## What are Stages?

**Stages** are sets of tasks that can be computed without shuffling data across partitions. Spark automatically divides the DAG into stages based on transformations that require shuffling.

### Stage Boundaries
- **Stage boundaries** are created by **wide transformations**
- Each wide transformation creates a new stage
- Narrow transformations within a stage can be pipelined together

### Example
```scala
val rdd1 = sc.textFile("file.txt")           // Stage 0 starts
val rdd2 = rdd1.map(_.toUpperCase)           // Still Stage 0 (narrow)
val rdd3 = rdd2.filter(_.contains("SPARK"))  // Still Stage 0 (narrow)
val rdd4 = rdd3.groupByKey()                 // Stage 1 starts (wide - shuffle)
val rdd5 = rdd4.map(x => (x._1, x._2.size))  // Still Stage 1 (narrow)
```

## What are Tasks?

**Tasks** are the smallest unit of execution in Spark. Each task processes one partition of data.

### Task Characteristics
- **One task per partition** in each stage
- Tasks run in parallel across different executor cores
- Tasks of the same stage can run simultaneously
- Tasks are **scheduled by the driver** and **executed by executors**

### Task Lifecycle
1. **Creation**: Driver creates tasks based on partitions
2. **Scheduling**: TaskScheduler assigns tasks to executors
3. **Execution**: Executor runs the task on its partition
4. **Completion**: Results sent back to driver

## Stage Types

### ShuffleMapStage
- **Intermediate stages** that produce shuffle data
- Output is written to local disk for shuffle
- Followed by other stages

### ResultStage
- **Final stage** that produces the result
- Directly returns results to driver program
- Triggered by actions like `collect()`, `count()`

## Task Types

### ShuffleMapTask
- Tasks in **ShuffleMapStages**
- Write intermediate results to local disk
- Results are shuffled to next stage

### ResultTask
- Tasks in **ResultStages** 
- Return final results to driver
- No shuffle output required

## Example Execution Flow

```scala
val data = sc.textFile("large_file.txt")     // 100 partitions
val words = data.flatMap(_.split(" "))       // Still 100 partitions
val pairs = words.map(word => (word, 1))     // Still 100 partitions
val counts = pairs.reduceByKey(_ + _)        // Shuffle! New stage
counts.collect()                             // Action triggers execution
```

### Stages Created:
- **Stage 0**: textFile → flatMap → map (100 ShuffleMapTasks)
- **Stage 1**: reduceByKey → collect (200 ResultTasks, assuming default parallelism)

## Monitoring Stages and Tasks

### Spark UI - Stages Tab
- View all stages in your application
- See task distribution and timing
- Identify bottlenecks and skewed partitions

### Key Metrics
- **Task Duration**: How long each task takes
- **Shuffle Read/Write**: Data movement between stages  
- **GC Time**: Garbage collection overhead
- **Serialization Time**: Object serialization costs

## Best Practices

### Minimize Stages
- Avoid unnecessary wide transformations
- Use `reduceByKey()` instead of `groupByKey().map()`
- Chain narrow transformations together

### Optimize Task Distribution
- Ensure even partition sizes
- Monitor for task skew
- Use appropriate number of partitions

### Stage Failure Recovery
- Failed stages are automatically retried
- Only failed tasks within a stage are re-executed
- Lineage information enables fault tolerance

## Common Issues

### Stage Skew
```scala
// Problem: Uneven data distribution
val skewed = data.groupByKey()  // Some partitions much larger

// Solution: Use salting or repartitioning
val balanced = data.repartition(numPartitions).groupByKey()
```

### Too Many Small Tasks
```scala
// Problem: Too many partitions = scheduling overhead
val manyPartitions = data.repartition(10000)

// Solution: Use optimal partition count
val optimal = data.coalesce(spark.defaultParallelism * 2)
```

## Summary

| Component | Definition | Key Points |
|-----------|------------|------------|
| **Stage** | Set of tasks with no shuffle boundary | Created by wide transformations |
| **Task** | Smallest execution unit | One per partition per stage |
| **ShuffleMapStage** | Intermediate stage | Produces shuffle data |
| **ResultStage** | Final stage | Returns results to driver |
| **ShuffleMapTask** | Task in shuffle stage | Writes to local disk |
| **ResultTask** | Task in result stage | Returns final results |
