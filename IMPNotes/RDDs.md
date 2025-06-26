# RDDs (Resilient Distributed Datasets)

## Definition
**RDD** = Resilient Distributed Dataset - the fundamental abstraction in Apache Spark. It represents an **immutable**, **distributed** collection of objects that can be processed in **parallel** across the cluster.

## Key Properties
- **Resilient**: Fault-tolerant through lineage information
- **Distributed**: Spread across multiple nodes in the cluster
- **Immutable**: Cannot be changed once created (transformations create new RDDs)
- **Lazy Evaluation**: Transformations are not executed until an action is called

## Creating RDDs
```scala
// From existing collections
val data = Array(1, 2, 3, 4, 5)
val rdd = sc.parallelize(data)

// From external datasets
val textRDD = sc.textFile("hdfs://path/to/file.txt")

// From other RDDs through transformations
val filteredRDD = textRDD.filter(_.contains("error"))
```

## RDD Lineage
Each RDD maintains information about how it was derived from other RDDs, creating a **lineage graph**. This enables:
- **Fault tolerance**: Lost partitions can be recomputed
- **Optimization**: Spark can optimize the execution plan
- **Lazy evaluation**: Operations are batched for efficiency

## When to Use RDDs
- Low-level data manipulation
- Working with unstructured data
- Need for fine-grained control over data distribution
- Working with data that doesn't fit well into DataFrames/Datasets

## RDD vs DataFrame/Dataset
| Feature | RDD | DataFrame/Dataset |
|---------|-----|-------------------|
| Type Safety | Compile-time (Scala/Java) | Runtime errors possible |
| Optimization | Manual | Automatic (Catalyst) |
| Performance | Good | Better (Tungsten) |
| API | Functional | SQL-like + Functional |
