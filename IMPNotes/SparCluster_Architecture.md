# Spark Cluster Architecture

## Overview

Apache Spark follows a **master-slave architecture** with a central coordinator (Driver) and distributed workers (Executors). Understanding this architecture is crucial for optimization and troubleshooting.

## Core Components

### 1. Driver Program
**The brain of the Spark application**

#### Responsibilities
- **SparkContext creation**: Entry point for Spark functionality
- **DAG construction**: Builds the execution graph
- **Task scheduling**: Decides which tasks run where
- **Result collection**: Gathers results from executors
- **Resource coordination**: Manages cluster resources

#### Key Processes
- **DAGScheduler**: Converts logical DAG into physical execution plan
- **TaskScheduler**: Assigns tasks to specific executors
- **BlockManager**: Manages data storage and retrieval

#### Driver Memory Usage
```scala
// Driver memory configuration
spark.driver.memory = 2g
spark.driver.maxResultSize = 1g  // Max size of results collected to driver
```

### 2. Executors
**The workers that execute tasks**

#### Responsibilities
- **Task execution**: Run individual tasks on data partitions
- **Data storage**: Cache/persist RDDs and DataFrames
- **Shuffle data**: Participate in data redistribution
- **Result reporting**: Send task results back to driver

#### Executor Processes
- **Executor JVM**: Runs the actual computation
- **Block Manager**: Manages local data storage
- **Shuffle Service**: Handles shuffle data (optional external service)

#### Executor Configuration
```scala
spark.executor.instances = 10      // Number of executors
spark.executor.cores = 4           // CPU cores per executor  
spark.executor.memory = 8g         // Memory per executor
```

### 3. Cluster Manager
**Resource manager for the cluster**

#### Types of Cluster Managers

##### Standalone
- **Built-in cluster manager** that comes with Spark
- Simple to set up and manage
- Good for dedicated Spark clusters

##### YARN (Yet Another Resource Negotiator)
- **Hadoop's resource manager**
- Integrates well with Hadoop ecosystem
- Supports multi-tenancy

##### Mesos
- **General-purpose cluster manager**
- Fine-grained resource sharing
- Good for mixed workloads

##### Kubernetes
- **Container orchestration platform**
- Cloud-native deployments
- Modern containerized environments

## Application Execution Flow

### 1. Application Submission
```bash
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --executor-memory 4g \
  --executor-cores 2 \
  --num-executors 20 \
  my-spark-app.py
```

### 2. Resource Allocation
```
1. Driver contacts Cluster Manager
2. Cluster Manager allocates resources
3. Executors are launched on worker nodes
4. Executors register with Driver
```

### 3. Task Execution
```
1. Driver creates DAG from transformations
2. DAG is divided into stages and tasks
3. Tasks are serialized and sent to executors
4. Executors execute tasks on local partitions
5. Results are sent back to driver
```

## Deploy Modes

### Client Mode
- **Driver runs on the client machine**
- Good for interactive applications (spark-shell, notebooks)
- Driver failure = application failure
- Network overhead for task scheduling

```bash
spark-submit --deploy-mode client my-app.py
```

### Cluster Mode  
- **Driver runs on one of the worker nodes**
- Good for production batch jobs
- More fault-tolerant
- Reduced network overhead

```bash
spark-submit --deploy-mode cluster my-app.py
```

### Comparison
| Feature | Client Mode | Cluster Mode |
|---------|-------------|--------------|
| Driver Location | Client machine | Worker node |
| Fault Tolerance | ❌ Lower | ✅ Higher |
| Network Usage | ❌ Higher | ✅ Lower |
| Interactive Use | ✅ Better | ❌ Limited |
| Production Use | ❌ Limited | ✅ Better |

## Network Communication

### Driver-Executor Communication
- **Bidirectional communication** required
- Driver sends tasks and receives results
- Executors send heartbeats and status updates

### Executor-Executor Communication
- **Shuffle operations** require inter-executor communication
- Data transfer during wide transformations
- Can be expensive over slow networks

### Network Optimization
```conf
# Serialization (faster over network)
spark.serializer = org.apache.spark.serializer.KryoSerializer

# Compression (reduces network traffic)
spark.sql.adaptive.enabled = true
spark.sql.adaptive.coalescePartitions.enabled = true

# Network timeout settings
spark.network.timeout = 300s
spark.executor.heartbeatInterval = 30s
```

## Data Locality

### Locality Levels (Best to Worst)
1. **PROCESS_LOCAL**: Data in same JVM process
2. **NODE_LOCAL**: Data on same physical node
3. **RACK_LOCAL**: Data in same server rack
4. **ANY**: Data anywhere in cluster

### Achieving Good Locality
```scala
// Partition data by frequently-joined keys
val partitionedDF = df.repartition($"user_id")

// Co-locate related datasets
val broadcastMap = sc.broadcast(smallLookupTable)
```

## Dynamic Allocation

### What is Dynamic Allocation?
- **Automatically adjust** the number of executors based on workload
- **Scale up** when tasks are pending
- **Scale down** when executors are idle

### Configuration
```conf
# Enable dynamic allocation
spark.dynamicAllocation.enabled = true
spark.dynamicAllocation.minExecutors = 2
spark.dynamicAllocation.maxExecutors = 20
spark.dynamicAllocation.initialExecutors = 5

# Scaling behavior
spark.dynamicAllocation.executorIdleTimeout = 60s
spark.dynamicAllocation.schedulerBacklogTimeout = 5s
```

### Benefits
- **Resource efficiency**: Only use what you need
- **Cost optimization**: Especially important in cloud environments
- **Automatic tuning**: Less manual configuration required

## Resource Isolation

### Executor Isolation
- Each executor runs in separate JVM process
- **Memory isolation**: Executor failures don't affect others
- **CPU isolation**: Configured cores per executor

### Application Isolation
- Different Spark applications don't interfere
- **Resource pools**: Can be configured for multi-tenancy
- **Queue management**: Fair sharing of cluster resources

## Monitoring and Debugging

### Spark UI Sections

#### Jobs Tab
- View all jobs and their stages
- See task distribution and timing
- Identify slow or failed tasks

#### Stages Tab  
- Detailed stage information
- Task-level metrics and timings
- Input/output data sizes

#### Storage Tab
- Cached RDDs and DataFrames
- Memory usage per executor
- Cache hit ratios

#### Executors Tab
- Executor resource utilization
- Task counts and timing
- Shuffle read/write metrics

#### SQL Tab (for DataFrames/SQL)
- Query execution plans
- Physical plan visualization
- Query timing breakdown

### Key Metrics to Monitor
```bash
# Resource utilization
CPU Usage per Executor
Memory Usage per Executor  
Disk I/O per Node

# Performance metrics
Task Duration Distribution
Shuffle Read/Write Sizes
GC Time per Executor

# Health metrics
Failed Task Count
Executor Failures
Driver Memory Usage
```

## Common Architecture Issues

### 1. Driver Bottlenecks
```scala
// Problem: Collecting large results to driver
val allData = largeDF.collect()  // ❌ Don't do this

// Solution: Process data distributed
largeDF.write.mode("overwrite").parquet("output/")  // ✅ Better
```

### 2. Executor Resource Imbalance
```scala
// Problem: Uneven partition sizes
val skewedData = df.groupBy("popular_key")

// Solution: Add randomization
val balanced = df.repartition(200, $"popular_key", rand())
```

### 3. Network Overhead
```scala
// Problem: Excessive shuffling
val result = df1.join(df2).groupBy("key").sum()

// Solution: Broadcast small tables
val result = df1.join(broadcast(df2)).groupBy("key").sum()
```

## Best Practices

### Resource Sizing
```conf
# General guidelines
# Executor memory: 2-8 GB per executor (avoid very large heaps)
# Executor cores: 2-5 cores per executor (diminishing returns beyond 5)
# Total executors: Depends on data size and cluster size

# Example balanced configuration
spark.executor.memory = 4g
spark.executor.cores = 3
spark.executor.instances = 20
```

### Application Design
```scala
// Minimize driver operations
// ❌ Avoid
val count = largeRDD.collect().length

// ✅ Better  
val count = largeRDD.count()

// Optimize data locality
// ❌ Many small files
largeDF.write.mode("overwrite").csv("output/")

// ✅ Fewer larger files
largeDF.coalesce(10).write.mode("overwrite").csv("output/")
```

### Cluster Configuration
```conf
# For long-running applications
spark.sql.adaptive.enabled = true
spark.dynamicAllocation.enabled = true

# For batch processing
spark.serializer = org.apache.spark.serializer.KryoSerializer
spark.sql.adaptive.coalescePartitions.enabled = true

# For streaming applications  
spark.streaming.dynamicAllocation.enabled = false  # Often better to use fixed resources
```

## Troubleshooting Guide

### Slow Jobs
1. **Check task distribution**: Are tasks evenly distributed?
2. **Monitor GC**: Is garbage collection excessive?
3. **Check data locality**: Are tasks running close to data?
4. **Analyze shuffles**: Are there unnecessary wide transformations?

### Memory Issues
1. **Driver OOM**: Reduce result collection, increase driver memory
2. **Executor OOM**: Increase executor memory, reduce partition size
3. **GC pressure**: Use off-heap storage, tune GC settings

### Network Issues  
1. **Slow shuffles**: Check network bandwidth, reduce shuffle data
2. **Timeouts**: Increase network timeout settings
3. **Connectivity**: Ensure all nodes can communicate
