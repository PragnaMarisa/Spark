# Joins in Apache Spark

## Overview
Joins are one of the most important and expensive operations in Spark. Understanding different join types and their implementation strategies is crucial for performance optimization.

## Join Types

### Inner Join
- Returns only matching rows from both datasets
- **Default join type** in Spark
```scala
df1.join(df2, "common_column")
df1.join(df2, df1("id") === df2("user_id"))
```

### Left Outer Join
- Returns all rows from left dataset, matching rows from right
- Non-matching rows from right side filled with null
```scala
df1.join(df2, "common_column", "left_outer")
df1.join(df2, df1("id") === df2("user_id"), "left")
```

### Right Outer Join
- Returns all rows from right dataset, matching rows from left
- Non-matching rows from left side filled with null
```scala
df1.join(df2, "common_column", "right_outer")
df1.join(df2, df1("id") === df2("user_id"), "right")
```

### Full Outer Join
- Returns all rows from both datasets
- Non-matching rows filled with null
```scala
df1.join(df2, "common_column", "full_outer")
df1.join(df2, df1("id") === df2("user_id"), "outer")
```

### Left Semi Join
- Returns rows from left dataset that have matches in right dataset
- Only columns from left dataset are returned
```scala
df1.join(df2, "common_column", "left_semi")
```

### Left Anti Join
- Returns rows from left dataset that have **no matches** in right dataset
- Opposite of left semi join
```scala
df1.join(df2, "common_column", "left_anti")
```

### Cross Join (Cartesian Product)
- Returns Cartesian product of both datasets
- **⚠️ Use with extreme caution** - O(n × m) complexity
```scala
df1.crossJoin(df2)
```

## Join Implementation Strategies

### 1. Broadcast Hash Join (BHJ)
**Best Performance** - When one dataset is small enough to fit in memory

#### Characteristics:
- **No shuffle required** - most efficient
- Small dataset is **broadcast** to all executors
- Each executor performs join locally
- **Memory requirement**: Small dataset must fit in executor memory

#### When Spark Chooses BHJ:
- One side is smaller than `spark.sql.autoBroadcastJoinThreshold` (default: 10MB)
- Can be forced using `broadcast()` function

```scala
// Automatic broadcast (if under threshold)
large_df.join(small_df, "key")

// Explicit broadcast
import org.apache.spark.sql.functions.broadcast
large_df.join(broadcast(small_df), "key")
```

#### Configuration:
```scala
// Increase broadcast threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "50MB")

// Disable broadcast joins
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", -1)
```

### 2. Sort Merge Join (SMJ)
**Default for large datasets** - When both datasets are large

#### Characteristics:
- Both datasets are **sorted** by join key
- **Shuffle required** if data not already partitioned by join key
- **Memory efficient** - processes data in sorted order
- Good for **equi-joins** (equality conditions)

#### Process:
1. Shuffle both datasets by join key (if needed)
2. Sort both datasets by join key
3. Merge sorted datasets

```scala
// Spark automatically chooses SMJ for large-large joins
large_df1.join(large_df2, "key")
```

### 3. Shuffle Hash Join (SHJ)
**When sort merge join is not optimal**

#### Characteristics:
- **Shuffle required** for both datasets
- Builds **hash table** from smaller dataset
- No sorting required
- More memory intensive than SMJ

#### When Spark Chooses SHJ:
- One side is smaller but not small enough for broadcast
- Sorting is expensive
- Can be forced with configuration

```scala
// Force shuffle hash join
spark.conf.set("spark.sql.join.preferSortMergeJoin", "false")
```

### 4. Cartesian Join
**Avoid unless necessary** - O(n × m) complexity

#### Characteristics:
- **No join condition** or **non-equi join**
- Every row from first dataset paired with every row from second
- **Extremely expensive** for large datasets

```scala
// Explicit cartesian join
df1.crossJoin(df2)

// Implicit cartesian (no join condition)
df1.join(df2) // Spark will warn about this
```

## Join Strategy Selection

### Decision Flow:
```
1. Check broadcast threshold
   ├─ Small dataset → Broadcast Hash Join
   └─ Both large → Continue
   
2. Check join type and conditions
   ├─ Equi-join → Sort Merge Join (default)
   ├─ Non-equi join → Cartesian Join
   └─ Forced config → Shuffle Hash Join
```

### Performance Comparison:
| Join Strategy | Shuffle Required | Memory Usage | Best For |
|---------------|------------------|--------------|----------|
| **Broadcast Hash** | ❌ No | Low | Small × Large |
| **Sort Merge** | ✅ Yes | Medium | Large × Large |
| **Shuffle Hash** | ✅ Yes | High | Medium × Large |
| **Cartesian** | ✅ Yes | Very High | ⚠️ Avoid |

## Join Optimization Techniques

### 1. Broadcast Optimization
```scala
// Check dataset size before join
val smallDfSize = small_df.count()
if (smallDfSize < 1000000) {
  large_df.join(broadcast(small_df), "key")
} else {
  large_df.join(small_df, "key")
}
```

### 2. Pre-partitioning
```scala
// Partition datasets by join key to avoid shuffle
val partitioned_df1 = df1.repartition($"join_key")
val partitioned_df2 = df2.repartition($"join_key")
partitioned_df1.join(partitioned_df2, "join_key")
```

### 3. Bucketing
```scala
// Pre-bucket tables to avoid shuffle in joins
df1.write
  .bucketBy(10, "join_key")
  .saveAsTable("bucketed_table1")

df2.write
  .bucketBy(10, "join_key")
  .saveAsTable("bucketed_table2")

// Join bucketed tables (no shuffle needed)
spark.table("bucketed_table1")
  .join(spark.table("bucketed_table2"), "join_key")
```

### 4. Join Condition Optimization
```scala
// Efficient: Use column names when possible
df1.join(df2, "common_column")

// Less efficient: Explicit column references
df1.join(df2, df1("id") === df2("id"))

// Avoid: Complex join conditions
df1.join(df2, df1("id") === df2("id") && df1("status") === "active")
```

## Join Performance Tuning

### Configuration Parameters:
```scala
// Broadcast threshold
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10MB")

// Prefer sort merge join
spark.conf.set("spark.sql.join.preferSortMergeJoin", "true")

// Adaptive query execution
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
```

### Monitoring Join Performance:
```scala
// Check query plan
df1.join(df2, "key").explain(true)

// Monitor through Spark UI
// - SQL tab shows join strategy
// - Stages tab shows shuffle operations
```

## Common Join Patterns

### 1. Dimension Table Joins
```scala
// Large fact table + small dimension table
fact_table.join(broadcast(dimension_table), "dimension_id")
```

### 2. Aggregation Before Join
```scala
// Reduce data size before expensive join
val aggregated = large_df
  .groupBy("key")
  .agg(sum("value").as("total_value"))

result_df.join(aggregated, "key")
```

### 3. Multiple Joins
```scala
// Chain joins efficiently
df1
  .join(broadcast(small_df1), "key1")
  .join(df2, "key2")
  .join(broadcast(small_df2), "key3")
```

## Best Practices

### Do's:
1. **Use broadcast joins** for small datasets (< 100MB)
2. **Pre-partition data** by join keys when possible
3. **Filter before join** to reduce data size
4. **Use bucketing** for repeated joins on same keys
5. **Monitor join strategies** in Spark UI

### Don'ts:
1. **Avoid cartesian joins** unless absolutely necessary
2. **Don't broadcast large datasets** (causes OOM errors)
3. **Don't ignore data skew** in join keys
4. **Don't use complex join conditions** unnecessarily
5. **Don't forget to cache** intermediate results in multi-step joins

### Data Skew Handling:
```scala
// Detect skew
df.groupBy("join_key").count().orderBy(desc("count")).show()

// Handle skew with salting
import org.apache.spark.sql.functions._
val salted_df = df.withColumn("salted_key", 
  concat($"join_key", lit("_"), (rand() * 10).cast("int")))
```

## Join Hints (Spark 3.0+)

```scala
// Force broadcast join
df1.hint("broadcast").join(df2, "key")

// Force sort merge join
df1.hint("merge").join(df2, "key")

// Force shuffle hash join
df1.hint("shuffle_hash").join(df2, "key")
```
