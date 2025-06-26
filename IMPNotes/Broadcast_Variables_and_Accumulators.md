# Broadcast Variables and Accumulators

## Broadcast Variables

### What are Broadcast Variables?
**Broadcast variables** allow efficient sharing of **small, read-only data** across all executors in a Spark cluster. They avoid sending data repeatedly with every task.

### Problem Without Broadcast
```scala
val lookupMap = Map("A" -> 1, "B" -> 2, "C" -> 3)  // Small lookup table

// BAD: This sends lookupMap with every task
val result = largeRDD.map { record =>
  lookupMap.getOrElse(record.category, 0)  // lookupMap sent to each task
}
```

### Solution With Broadcast
```scala
val lookupMap = Map("A" -> 1, "B" -> 2, "C" -> 3)
val broadcastLookup = sc.broadcast(lookupMap)  // Broadcast once

// GOOD: lookupMap sent once per executor, reused by all tasks
val result = largeRDD.map { record =>
  broadcastLookup.value.getOrElse(record.category, 0)  // Access broadcast value
}

broadcastLookup.destroy()  // Clean up when done
```

### Benefits
| Without Broadcast | With Broadcast |
|------------------|----------------|
| Data sent with **every task** | Data sent **once per executor** |
| High network overhead | Minimal network overhead |
| Slower execution | **Faster execution** |
| Higher memory usage | **Lower memory usage** |

---

## Broadcast Use Cases

### 1. Lookup Tables
```scala
val productCatalog = spark.read.table("product_catalog")
  .collect()  // Small table to driver
  .map(row => row.getString(0) -> row.getString(1))
  .toMap

val broadcastCatalog = sc.broadcast(productCatalog)

val enrichedData = salesData.map { sale =>
  val productName = broadcastCatalog.value.getOrElse(sale.productId, "Unknown")
  (sale, productName)
}
```

### 2. Configuration Maps
```scala
val configMap = Map(
  "threshold" -> 100,
  "multiplier" -> 1.5,
  "enabled" -> true
)
val broadcastConfig = sc.broadcast(configMap)

val processedData = rawData.filter { record =>
  record.value > broadcastConfig.value("threshold").asInstanceOf[Int]
}
```

### 3. ML Model Parameters
```scala
val modelWeights = trainedModel.getWeights  // Small array
val broadcastWeights = sc.broadcast(modelWeights)

val predictions = testData.map { features =>
  predict(features, broadcastWeights.value)
}
```

---

## Broadcast Best Practices

### Size Considerations
- **Ideal size**: < 100 MB per broadcast variable
- **Maximum recommended**: < 1 GB
- **Too large**: Can cause memory issues and slow startup

### Memory Management
```scala
// Always destroy when no longer needed
val broadcast = sc.broadcast(data)
// ... use broadcast
broadcast.destroy()  // Free memory across cluster
```

### DataFrame Broadcast Join
```scala
import org.apache.spark.sql.functions.broadcast

val largeDf = spark.read.table("large_table")
val smallDf = spark.read.table("small_table")  // < 10MB

// Explicit broadcast join
val result = largeDf.join(broadcast(smallDf), "key")

// Auto broadcast (configurable threshold)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "10MB")
```

---

## Accumulators

### What are Accumulators?
**Accumulators** are variables used for collecting global metrics or debugging information. They are **write-only from tasks** and **read-only from the driver**.

### Characteristics
| Feature | Tasks (Executors) | Driver |
|---------|------------------|--------|
| **Write** | ✅ Yes (via `add()`) | ✅ Yes |
| **Read** | ❌ No | ✅ Yes |
| **Use case** | Increment counters | Read final values |

### Basic Usage
```scala
// Create accumulator
val errorCount = sc.longAccumulator("Error Counter")
val validRecords = sc.longAccumulator("Valid Records")

val processedData = rawData.map { record =>
  if (record.isValid) {
    validRecords.add(1)
    process(record)
  } else {
    errorCount.add(1)
    null
  }
}.filter(_ != null)

// Trigger action to execute
processedData.collect()

// Read results in driver
println(s"Total errors: ${errorCount.value}")
println(s"Valid records: ${validRecords.value}")
```

---

## Types of Accumulators

### Built-in Accumulators
```scala
// Numeric accumulators
val longAcc = sc.longAccumulator("Long Counter")
val doubleAcc = sc.doubleAccumulator("Double Sum")

// Collection accumulator
val listAcc = sc.collectionAccumulator[String]("String Collection")

data.foreach { record =>
  longAcc.add(1)
  doubleAcc.add(record.value)
  if (record.hasError) listAcc.add(record.errorMessage)
}
```

### Custom Accumulators
```scala
import org.apache.spark.util.AccumulatorV2

class SetAccumulator extends AccumulatorV2[String, Set[String]] {
  private var _set = Set.empty[String]
  
  def isZero: Boolean = _set.isEmpty
  def copy(): SetAccumulator = {
    val acc = new SetAccumulator
    acc._set = _set
    acc
  }
  def reset(): Unit = _set = Set.empty
  def add(v: String): Unit = _set += v
  def merge(other: AccumulatorV2[String, Set[String]]): Unit = {
    _set ++= other.value
  }
  def value: Set[String] = _set
}

// Usage
val uniqueErrors = new SetAccumulator
sc.register(uniqueErrors, "Unique Errors")

data.foreach { record =>
  if (record.hasError) uniqueErrors.add(record.errorType)
}
```

---

## Accumulator Use Cases

### 1. Debugging and Monitoring
```scala
val malformedRecords = sc.longAccumulator("Malformed Records")
val processedRecords = sc.longAccumulator("Processed Records")

val cleanData = rawData.mapPartitions { partition =>
  partition.map { record =>
    try {
      val parsed = parseRecord(record)
      processedRecords.add(1)
      Some(parsed)
    } catch {
      case _: Exception =>
        malformedRecords.add(1)
        None
    }
  }.flatten
}

cleanData.collect()
println(s"Processed: ${processedRecords.value}, Malformed: ${malformedRecords.value}")
```

### 2. Quality Metrics
```scala
val qualityMetrics = Map(
  "high_quality" -> sc.longAccumulator("High Quality"),
  "medium_quality" -> sc.longAccumulator("Medium Quality"),
  "low_quality" -> sc.longAccumulator("Low Quality")
)

data.foreach { record =>
  val quality = calculateQuality(record)
  quality match {
    case q if q > 0.8 => qualityMetrics("high_quality").add(1)
    case q if q > 0.5 => qualityMetrics("medium_quality").add(1)
    case _ => qualityMetrics("low_quality").add(1)
  }
}
```

### 3. Performance Profiling
```scala
val processingTime = sc.doubleAccumulator("Total Processing Time")

val result = data.map { record =>
  val startTime = System.currentTimeMillis()
  val processed = expensiveOperation(record)
  val endTime = System.currentTimeMillis()
  
  processingTime.add(endTime - startTime)
  processed
}

result.collect()
println(s"Average processing time: ${processingTime.value / data.count()} ms")
```

---

## Important Considerations

### Accumulator Guarantees
- **Actions only**: Accumulators only updated reliably in **actions**, not transformations
- **Task retries**: May cause duplicate updates if tasks are retried
- **Lazy evaluation**: Updates happen only when action is executed

### Example of Potential Issues
```scala
val counter = sc.longAccumulator("Counter")

// PROBLEMATIC: Updates in transformation
val mapped = data.map { x =>
  counter.add(1)  // May be executed multiple times due to retries
  x * 2
}

// Better approach: Update in foreach (action)
data.foreach { x =>
  counter.add(1)  // Executed exactly once per record
  processRecord(x)
}
```

### Best Practices
1. **Use in actions**: Prefer `foreach()` over `map()` for accumulator updates
2. **Idempotent operations**: Design updates to be safe if executed multiple times
3. **Named accumulators**: Always provide meaningful names for debugging
4. **Resource cleanup**: Not strictly required but good practice

```scala
// Good pattern
val errorCounter = sc.longAccumulator("Processing Errors")

data.foreach { record =>
  try {
    processRecord(record)
  } catch {
    case _: Exception => errorCounter.add(1)
  }
}

println(s"Total errors: ${errorCounter.value}")
```
