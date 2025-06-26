# Dependencies: Narrow vs Wide

## Narrow Dependencies
**Definition**: Each partition of child RDD depends on **at most one partition** of parent RDD.

### Characteristics
- **No shuffling needed** - data stays on the same node
- **Pipelined execution** - Spark can combine multiple operations
- **Faster execution** - minimal network overhead
- **Better fault tolerance** - failures affect fewer partitions

### Examples of Narrow Transformations
```scala
val rdd = sc.parallelize(1 to 100, 4)

// Each output partition depends on exactly one input partition
val mapped = rdd.map(x => x * 2)           // map()
val filtered = rdd.filter(x => x > 50)     // filter()  
val sampled = rdd.sample(false, 0.5)       // sample()

// Union combines partitions but maintains 1:1 relationship
val combined = rdd1.union(rdd2)            // union()
```

### Visual Representation
```
Input Partitions:  [P1] [P2] [P3] [P4]
                    |    |    |    |
                    ↓    ↓    ↓    ↓
Output Partitions: [P1'] [P2'] [P3'] [P4']
```

## Wide Dependencies
**Definition**: Each partition of child RDD depends on **multiple partitions** of parent RDD.

### Characteristics
- **Shuffling required** - data moves across the network
- **Stage boundaries** - creates breaks in the execution pipeline
- **Slower execution** - network and disk I/O overhead
- **Resource intensive** - requires coordination across executors

### Examples of Wide Transformations
```scala
val keyValueRDD = sc.parallelize(List(("a", 1), ("b", 2), ("a", 3), ("c", 4)))

// These operations require grouping data by key across partitions
val grouped = keyValueRDD.groupByKey()           // groupByKey()
val reduced = keyValueRDD.reduceByKey(_ + _)     // reduceByKey()
val distinct = keyValueRDD.distinct()            // distinct()

// Joins require matching keys from both RDDs
val joined = rdd1.join(rdd2)                     // join()

// Repartitioning explicitly reshuffles data
val repartitioned = rdd.repartition(8)           // repartition()
```

### Visual Representation
```
Input Partitions:  [P1] [P2] [P3] [P4]
                    \   / \   / \   /
                     \ /   \ /   \ /
                      X     X     X    ← Shuffle
                     / \   / \   / \
Output Partitions: [P1'] [P2'] [P3'] [P4']
```

## Comparison Summary

| Feature | Narrow Dependency | Wide Dependency |
|---------|-------------------|-----------------|
| **Partition Mapping** | One-to-one or one-to-few | Many-to-many |
| **Shuffle Required?** | ❌ No | ✅ Yes |
| **Speed** | 🚀 Fast | 🐢 Slower |
| **Pipeline-able?** | ✅ Yes | ❌ No |
| **Stage Break** | ❌ No | ✅ Yes |
| **Network I/O** | Minimal | High |
| **Fault Tolerance** | Better | More complex |

## Performance Implications

### Narrow Transformations
- Can be **pipelined together** in the same stage
- **No network overhead** for data movement
- **Linear scalability** - adding more partitions improves performance
- **Faster recovery** from failures

### Wide Transformations
- Create **stage boundaries** in the DAG
- Require **shuffle operations** (expensive)
- May cause **data skew** if keys are not evenly distributed
- **Checkpointing recommended** for fault tolerance

## Optimization Tips
1. **Minimize wide transformations** when possible
2. **Use `reduceByKey()` instead of `groupByKey()`** - more efficient
3. **Partition data appropriately** to reduce shuffle
4. **Cache data** before expensive wide operations
5. **Use broadcast joins** for small datasets

## Stage Boundaries
Wide dependencies create **stage boundaries** because:
- Spark cannot pipeline operations across shuffles
- Each stage must complete before the next can begin
- Stages run independently and can be retried separately
