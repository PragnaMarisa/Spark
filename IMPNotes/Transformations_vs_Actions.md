# Transformations vs Actions

## Transformations
**Lazy operations** that define computation logic but don't execute immediately. They return new RDDs and build up a computation graph.

### Characteristics
- Return new RDDs
- Not executed immediately (lazy evaluation)
- Build up the DAG (Directed Acyclic Graph)
- No data movement until action is called

### Common Transformations
```scala
// Narrow transformations
val mapped = rdd.map(x => x * 2)
val filtered = rdd.filter(x => x > 10)
val flattened = rdd.flatMap(_.split(" "))

// Wide transformations  
val grouped = rdd.groupByKey()
val reduced = rdd.reduceByKey(_ + _)
val joined = rdd1.join(rdd2)
```

## Actions
**Eager operations** that trigger the execution of the entire computation graph. They return results to the driver program or write data to external storage.

### Characteristics
- Trigger execution of all preceding transformations
- Return concrete results (not RDDs)
- Can be expensive operations
- Results are sent back to the driver

### Common Actions
```scala
// Collecting results
val results = rdd.collect()          // Returns Array
val count = rdd.count()              // Returns Long
val first = rdd.first()              // Returns first element
val sample = rdd.take(10)            // Returns Array of 10 elements

// Aggregations
val sum = rdd.reduce(_ + _)           // Returns aggregated value
val min = rdd.min()                  // Returns minimum value

// Saving data
rdd.saveAsTextFile("hdfs://path/")   // Writes to storage
rdd.foreach(println)                 // Performs action on each element
```

## Execution Flow
1. **Build DAG**: Transformations create a logical execution plan
2. **Optimize**: Spark optimizes the DAG
3. **Execute**: Actions trigger the execution
4. **Return Results**: Results are returned to driver or saved

## Best Practices
- Chain transformations together for efficiency
- Use actions sparingly to avoid unnecessary computation
- Cache intermediate results if used multiple times
- Be aware that each action triggers full recomputation (unless cached)

## Example Workflow
```scala
val lines = sc.textFile("log.txt")              // Transformation
val errors = lines.filter(_.contains("ERROR"))   // Transformation  
val cached = errors.cache()                      // Transformation + Cache
val count = cached.count()                       // Action (triggers execution)
val samples = cached.take(10)                    // Action (uses cache)
```
