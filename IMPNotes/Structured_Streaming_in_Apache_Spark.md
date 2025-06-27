# Structured Streaming in Apache Spark

## Overview
**Structured Streaming** is a scalable and fault-tolerant stream processing engine built on Spark SQL. It treats streaming data as an **unbounded table** that is continuously appended to.

## Core Concepts

### Streaming as Unbounded Table
- **Input stream** = unbounded input table
- **Query on stream** = incremental SQL query on unbounded table
- **Result** = updated result table at every micro-batch

```
Input Stream → Unbounded Table → Query → Result Table → Output Stream
```

### Micro-batch Processing
- Stream is processed as series of small **micro-batches**
- Each micro-batch contains a batch of data from the stream
- Query is executed on each micro-batch incrementally

## Triggers

### What are Triggers?
**Triggers** control when and how often micro-batches are processed.

### Trigger Types

#### 1. Processing Time Trigger
```scala
.trigger(Trigger.ProcessingTime("10 seconds"))
```
- Process micro-batch **every N seconds/minutes**
- **Default behavior** if no trigger specified
- Good for regular interval processing

#### 2. Once Trigger
```scala
.trigger(Trigger.Once())
```
- Process **exactly one micro-batch** then stop
- Useful for batch-like processing of streaming data
- Good for testing and one-time data processing

#### 3. Continuous Trigger (Experimental)
```scala
.trigger(Trigger.Continuous("1 second"))
```
- **Low-latency processing** (experimental in Spark 2.3+)
- Provides end-to-end latencies as low as 1ms
- Limited operations supported

#### 4. Available Now Trigger (Spark 3.3+)
```scala
.trigger(Trigger.AvailableNow())
```
- Process all available data in multiple micro-batches
- Stop when no more data is available
- Like `Once` but handles backlog efficiently

### Trigger Comparison
| Trigger Type | Latency | Use Case | Stopping Behavior |
|-------------|---------|----------|-------------------|
| **ProcessingTime** | Seconds/Minutes | Regular processing | Runs continuously |
| **Once** | Batch-like | One-time processing | Stops after one batch |
| **Continuous** | Milliseconds | Ultra-low latency | Runs continuously |
| **AvailableNow** | Batch-like | Backlog processing | Stops when caught up |

## Basic Streaming Query Structure

```scala
val streamingDF = spark
  .readStream
  .format("kafka")           // Source
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("subscribe", "topic")
  .load()

val query = streamingDF
  .select(...)               // Transformations
  .writeStream
  .outputMode("append")      // Output mode
  .format("console")         // Sink
  .trigger(Trigger.ProcessingTime("10 seconds"))
  .start()

query.awaitTermination()
```

## Output Modes

### 1. Append Mode
- **Default mode**
- Only **newly added rows** are written to sink
- Works with queries that **don't have aggregations**
```scala
.outputMode("append")
```

### 2. Complete Mode
- **Entire result table** is written to sink after every micro-batch
- Works only with **aggregation queries**
- Expensive for large result sets
```scala
.outputMode("complete")
```

### 3. Update Mode
- Only **updated rows** are written to sink
- Works with **aggregation queries**
- More efficient than complete mode
```scala
.outputMode("update")
```

### Output Mode Compatibility
| Query Type | Append | Complete | Update |
|------------|--------|----------|--------|
| **No aggregation** | ✅ | ❌ | ❌ |
| **Aggregation** | ❌* | ✅ | ✅ |
| **Aggregation + Watermark** | ✅ | ✅ | ✅ |

*Append mode with aggregation requires watermarking

## Windowing Operations

### Time Windows
Group streaming data into time-based windows for aggregation.

```scala
import org.apache.spark.sql.functions._

// Tumbling window (non-overlapping)
streamingDF
  .groupBy(window($"timestamp", "10 minutes"))
  .count()

// Sliding window (overlapping)
streamingDF
  .groupBy(window($"timestamp", "10 minutes", "5 minutes"))
  .count()

// Session window (gap-based)
streamingDF
  .groupBy(session_window($"timestamp", "5 minutes"))
  .count()
```

### Window Types

#### 1. Tumbling Windows
- **Non-overlapping**, fixed-size windows
- Each event belongs to exactly one window
```scala
window($"timestamp", "10 minutes")
```

#### 2. Sliding Windows
- **Overlapping** windows
- Events can belong to multiple windows
```scala
window($"timestamp", "10 minutes", "5 minutes")
// 10-minute windows, sliding every 5 minutes
```

#### 3. Session Windows
- **Variable-size** windows based on activity
- Window closes after period of inactivity
```scala
session_window($"timestamp", "5 minutes")
```

## Watermarking

### What is Watermarking?
**Watermarking** handles **late-arriving data** by defining how late data can be before it's considered too late to process.

### Why Watermarking?
- **Bounded state**: Prevents infinite state growth
- **Late data handling**: Define acceptable lateness
- **Triggers output**: Determines when to emit results

### Setting Watermarks
```scala
streamingDF
  .withWatermark("timestamp", "10 minutes")  // Allow 10 minutes late
  .groupBy(window($"timestamp", "5 minutes"))
  .count()
```

### Watermark Behavior
```
Current Max Timestamp: 12:15
Watermark Delay: 10 minutes
Current Watermark: 12:05

Events with timestamp < 12:05 will be dropped
Events with timestamp >= 12:05 will be processed
```

## State Management

### Stateful Operations
Operations that need to maintain state across micro-batches:
- **Aggregations**: `groupBy().count()`, `sum()`, etc.
- **Joins**: Stream-stream joins, stream-static joins
- **Deduplication**: `dropDuplicates()`
- **Custom stateful**: `mapGroupsWithState()`, `flatMapGroupsWithState()`

### State Store
- **Distributed state store** maintains state across executors
- **Fault-tolerant** through checkpointing
- **Versioned** for exactly-once processing

## Stream-Stream Joins

### Inner Join
```scala
val stream1 = spark.readStream...
val stream2 = spark.readStream...

stream1.join(stream2, "key")
```

### Join with Time Constraints
```scala
stream1
  .withWatermark("timestamp1", "1 hour")
  .join(
    stream2.withWatermark("timestamp2", "2 hours"),
    expr("key1 = key2 AND timestamp1 >= timestamp2 - interval 1 hour AND timestamp1 <= timestamp2 + interval 30 minutes")
  )
```

### Join Types Supported
- **Inner joins** ✅
- **Left/Right outer joins** ✅ (with watermarks)
- **Full outer joins** ❌ (not supported)

## Checkpointing

### Purpose
- **Fault tolerance**: Recovery from failures
- **Exactly-once processing**: Maintains processing offsets
- **State recovery**: Restores stateful operations

### Setting Checkpoints
```scala
val query = streamingDF
  .writeStream
  .option("checkpointLocation", "/path/to/checkpoint")
  .start()
```

### Checkpoint Contents
- **Metadata**: Query configuration, schema
- **Offsets**: Source reading positions
- **State**: Aggregation state, join state

## Sources and Sinks

### Common Sources
```scala
// File source
spark.readStream.format("json").option("path", "/path").load()

// Kafka source
spark.readStream.format("kafka")
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("subscribe", "topic")
  .load()

// Socket source (testing only)
spark.readStream.format("socket")
  .option("host", "localhost")
  .option("port", 9999)
  .load()

// Rate source (testing)
spark.readStream.format("rate").option("rowsPerSecond", 10).load()
```

### Common Sinks
```scala
// Console sink (testing)
.writeStream.format("console").start()

// File sink
.writeStream.format("parquet").option("path", "/output").start()

// Kafka sink
.writeStream.format("kafka")
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("topic", "output-topic")
  .start()

// Memory sink (testing)
.writeStream.format("memory").queryName("tableName").start()

// ForeachBatch sink (custom)
.writeStream.foreachBatch { (batchDF, batchId) =>
  // Custom processing
}.start()
```

## Error Handling and Recovery

### Query Recovery
```scala
val query = streamingDF
  .writeStream
  .option("checkpointLocation", "/checkpoint")
  .start()

// Restart from checkpoint
query.stop()
val newQuery = streamingDF
  .writeStream
  .option("checkpointLocation", "/checkpoint")  // Same location
  .start()
```

### Error Handling Options
```scala
// Continue on data errors
.option("mode", "PERMISSIVE")

// Fail fast on errors  
.option("mode", "FAILFAST")

// Drop malformed records
.option("mode", "DROPMALFORMED")
```

## Monitoring Streaming Queries

### Query Progress
```scala
val query = streamingDF.writeStream.start()

// Get latest progress
val progress = query.lastProgress
println(s"Batch ID: ${progress.batchId}")
println(s"Input rows: ${progress.inputRowsPerSecond}")
println(s"Processing rate: ${progress.durationMs}")

// Progress stream
query.recentProgress.foreach(println)
```

### Streaming Metrics
- **Input rate**: Records/second from source
- **Processing rate**: Records processed/second  
- **Batch duration**: Time to process each batch
- **End-to-end latency**: Source to sink delay
- **State size**: Memory used for stateful operations

### Spark UI Monitoring
- **Streaming tab**: Query statistics, batch timelines
- **SQL tab**: Micro-batch query plans
- **Stages tab**: Task execution details

## Best Practices

### Performance Optimization
1. **Right-size micro-batches**: Balance latency vs throughput
2. **Use appropriate triggers**: Match business requirements
3. **Optimize watermarks**: Not too aggressive, not too lenient
4. **Partition streaming data**: Better parallelism
5. **Cache intermediate results**: For complex queries

### Fault Tolerance
1. **Always set checkpoint location**: Enable recovery
2. **Use reliable sources/sinks**: Kafka, cloud storage
3. **Handle schema evolution**: Plan for data changes
4. **Monitor query health**: Set up alerting

### Resource Management
1. **Appropriate cluster sizing**: Enough resources for peak load
2. **Manage state size**: Use watermarks, clean old state
3. **Control parallelism**: Right number of partitions
4. **Memory tuning**: Adequate memory for state storage

### Example: Complete Streaming Application
```scala
import org.apache.spark.sql.functions._
import org.apache.spark.sql.streaming.Trigger

val query = spark
  .readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("subscribe", "input-topic")
  .load()
  .select(
    from_json($"value".cast("string"), schema).as("data"),
    $"timestamp".as("kafka_timestamp")
  )
  .select("data.*", "kafka_timestamp")
  .withWatermark("kafka_timestamp", "10 minutes")
  .groupBy(
    window($"kafka_timestamp", "5 minutes"),
    $"category"
  )
  .agg(
    count("*").as("event_count"),
    avg("value").as("avg_value")
  )
  .writeStream
  .outputMode("update")
  .format("kafka")
  .option("kafka.bootstrap.servers", "localhost:9092")
  .option("topic", "output-topic")
  .option("checkpointLocation", "/checkpoint/location")
  .trigger(Trigger.ProcessingTime("30 seconds"))
  .start()

query.awaitTermination()
```
