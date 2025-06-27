# Spark Configuration and Tuning Parameters

## Overview
Apache Spark provides hundreds of configuration parameters to optimize performance, resource usage, and behavior. Understanding key configurations is crucial for production deployments.

## Configuration Hierarchy

### Configuration Precedence (Highest to Lowest)
1. **SparkConf in application code**
2. **Command-line flags** (`--conf`)
3. **spark-defaults.conf** file
4. **Environment variables**
5. **Built-in defaults**

```scala
// 1. In application code
val conf = new SparkConf()
  .setAppName("MyApp")
  .set("spark.executor.memory", "4g")

// 2. Command line
spark-submit --conf spark.executor.memory=4g myapp.jar

// 3. spark-defaults.conf
spark.executor.memory    4g
spark.executor.cores     2
```

## Core Configuration Categories

### 1. Application Properties

| Property | Default | Description |
|----------|---------|-------------|
| `spark.app.name` | None | Application name |
| `spark.master` | None | Cluster manager (local, yarn, k8s) |
| `spark.submit.deployMode` | client | Deploy mode (client/cluster) |
| `spark.driver.memory` | 1g | Driver memory |
| `spark.driver.cores` | 1 | Driver CPU cores |

```scala
val conf = new SparkConf()
  .setAppName("ProductionApp")
  .setMaster("yarn")
  .set("spark.submit.deployMode", "cluster")
```

### 2. Executor Configuration

| Property | Default | Description |
|----------|---------|-------------|
| `spark.executor.memory` | 1g | Executor heap memory |
| `spark.executor.cores` | 1 | CPU cores per executor |
| `spark.executor.instances` | 2 | Number of executors (static) |
| `spark.executor.memoryFraction` | 0.6 | Fraction for execution/storage |
| `spark.executor.memoryStorageFraction` | 0.5 | Storage memory fraction |

### 3. Dynamic Allocation

```properties
# Enable dynamic allocation
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=1
spark.dynamicAllocation.maxExecutors=20
spark.dynamicAllocation.initialExecutors=5

# Scaling parameters
spark.dynamicAllocation.executorIdleTimeout=60s
spark.dynamicAllocation.schedulerBacklogTimeout=1s
spark.dynamicAllocation.sustainedSchedulerBacklogTimeout=5s
```

### 4. Memory Management

#### Memory Regions Configuration
```properties
# Java heap settings
spark.executor.memory=8g
spark.driver.memory=4g

# Off-heap memory (for Tungsten)
spark.memory.offHeap.enabled=true
spark.memory.offHeap.size=2g

# Memory fractions
spark.memory.fraction=0.8              # Unified memory region
spark.memory.storageFraction=0.5       # Storage vs execution
```

#### Memory Calculation Example
```
Total Executor Memory = 8GB
├── Reserved Memory (300MB)
├── User Memory (20% = 1.54GB)  
└── Unified Memory (80% = 6.16GB)
    ├── Storage Memory (50% = 3.08GB)
    └── Execution Memory (50% = 3.08GB)
```

### 5. Shuffle Configuration

```properties
# Shuffle partitions (important for performance)
spark.sql.shuffle.partitions=200       # Default, often too low
spark.sql.adaptive.shuffle.targetPostShuffleInputSize=64MB

# Shuffle behavior
spark.shuffle.compress=true
spark.shuffle.spill.compress=true
spark.shuffle.service.enabled=true

# Shuffle optimization
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
```

### 6. Catalyst and SQL Configuration

```properties
# Query optimization
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
spark.sql.adaptive.skewJoin.enabled=true

# Broadcast joins
spark.sql.autoBroadcastJoinThreshold=10MB
spark.sql.broadcastTimeout=300s

# Caching
spark.sql.cache.serializer=org.apache.spark.serializer.KryoSerializer
```

### 7. Kryo Serialization

```properties
# Enable Kryo (faster than Java serialization)
spark.serializer=org.apache.spark.serializer.KryoSerializer
spark.kryo.unsafe=true
spark.kryo.registrationRequired=false

# Register custom classes for better performance
spark.kryo.classesToRegister=com.mycompany.MyClass1,com.mycompany.MyClass2
```

## Environment-Specific Configurations

### Development Environment
```properties
# Small cluster, fast feedback
spark.executor.memory=2g
spark.executor.cores=2
spark.executor.instances=2
spark.sql.shuffle.partitions=8
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

### Production Environment
```properties
# Large cluster, optimized performance
spark.executor.memory=8g
spark.executor.cores=4
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.maxExecutors=100
spark.sql.shuffle.partitions=800
spark.sql.adaptive.enabled=true
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

### Streaming Applications
```properties
# Structured Streaming optimizations
spark.sql.streaming.checkpointLocation=/path/to/checkpoint
spark.sql.streaming.stateStore.maintenanceInterval=60s
spark.executor.memory=4g
spark.streaming.dynamicAllocation.enabled=true
```

## Common Configuration Patterns

### 1. Resource Sizing Formula

```
Executor Memory = (Node Memory - OS Memory) / Executors per Node
Executor Cores = Node Cores / Executors per Node

# Example: 32GB node, 16 cores
# Leave 4GB for OS = 28GB available
# 2 executors per node = 14GB per executor
# 8 cores per executor

spark.executor.memory=14g
spark.executor.cores=8
```

### 2. Partition Sizing

```properties
# Target partition size: 100-200MB
# For shuffle operations, calculate based on data size

# Data size = 10GB, target partition = 128MB
# Partitions needed = 10GB / 128MB = ~80 partitions
spark.sql.shuffle.partitions=80
```

### 3. GC Tuning

```properties
# G1GC for better performance with large heaps
spark.executor.extraJavaOptions=-XX:+UseG1GC -XX:MaxGCPauseMillis=100
spark.driver.extraJavaOptions=-XX:+UseG1GC -XX:MaxGCPauseMillis=100

# Additional GC options
spark.executor.extraJavaOptions=-XX:+UseG1GC \
  -XX:MaxGCPauseMillis=100 \
  -XX:G1HeapRegionSize=32m \
  -XX:+PrintGCDetails \
  -XX:+PrintGCTimeStamps
```

## Configuration by Use Case

### 1. ETL Workloads
```properties
# Large files, complex transformations
spark.executor.memory=16g
spark.executor.cores=5
spark.sql.shuffle.partitions=400
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

### 2. Machine Learning
```properties
# Iterative algorithms, caching
spark.executor.memory=8g
spark.executor.cores=4
spark.storage.memoryFraction=0.8
spark.sql.execution.arrow.pyspark.enabled=true  # For PySpark
spark.serializer=org.apache.spark.serializer.KryoSerializer
```

### 3. Interactive Analytics
```properties
# Fast query response, small datasets
spark.executor.memory=4g
spark.executor.cores=2
spark.sql.adaptive.enabled=true
spark.sql.autoBroadcastJoinThreshold=50MB
spark.sql.cache.serializer=org.apache.spark.serializer.KryoSerializer
```

## Configuration Management

### 1. Using spark-defaults.conf
```properties
# /opt/spark/conf/spark-defaults.conf
spark.master                     yarn
spark.executor.memory            4g
spark.executor.cores             2
spark.sql.shuffle.partitions     200
spark.serializer                 org.apache.spark.serializer.KryoSerializer
spark.sql.adaptive.enabled       true
```

### 2. Application-Specific Configuration
```scala
val conf = new SparkConf()
  .setAppName("MyETLJob")
  .set("spark.executor.memory", "8g")
  .set("spark.executor.cores", "4")
  .set("spark.sql.shuffle.partitions", "400")

val spark = SparkSession.builder()
  .config(conf)
  .getOrCreate()
```

### 3. Runtime Configuration Updates
```scala
// Some configs can be changed at runtime
spark.conf.set("spark.sql.shuffle.partitions", "100")

// Check current configuration
val shufflePartitions = spark.conf.get("spark.sql.shuffle.partitions")
```

## Monitoring Configuration Impact

### 1. Spark UI Metrics
- **Executors Tab**: Memory usage, GC time
- **SQL Tab**: Query execution plans
- **Storage Tab**: Cached data size
- **Environment Tab**: All configuration values

### 2. Key Metrics to Watch
```scala
// Monitor these through Spark UI or programmatically
- Task execution time
- Shuffle read/write sizes
- GC time percentage
- Memory utilization
- Spill to disk frequency
```

### 3. Configuration Validation
```scala
// Validate configuration values
val executorMemory = spark.conf.get("spark.executor.memory")
val shufflePartitions = spark.conf.get("spark.sql.shuffle.partitions")

println(s"Executor Memory: $executorMemory")
println(s"Shuffle Partitions: $shufflePartitions")
```

## Best Practices

### 1. Start with Defaults, Then Tune
- Begin with reasonable defaults
- Monitor performance metrics
- Adjust one parameter at a time
- Document changes and their impact

### 2. Configuration Testing
```bash
# Test different configurations
spark-submit --conf spark.sql.shuffle.partitions=400 \
            --conf spark.executor.memory=8g \
            myapp.jar

# Compare performance metrics
```

### 3. Environment Consistency
- Use same configurations across dev/staging/prod
- Version control your configuration files
- Automate configuration deployment

### 4. Resource Planning
```
# Calculate cluster resources needed
Total Cores Needed = Parallelism × Average Task Time / SLA
Total Memory Needed = Data Size × Memory Multiplier

# Memory multiplier typically 2-3x for caching and intermediate data
```

## Common Configuration Mistakes

### 1. Too Many Small Executors
```properties
# ❌ Too many small executors
spark.executor.memory=1g
spark.executor.cores=1
spark.executor.instances=100

# ✅ Fewer larger executors  
spark.executor.memory=8g
spark.executor.cores=4
spark.executor.instances=25
```

### 2. Wrong Shuffle Partitions
```properties
# ❌ Default often too small for large datasets
spark.sql.shuffle.partitions=200

# ✅ Size based on data volume
spark.sql.shuffle.partitions=800  # For ~100GB dataset
```

### 3. Not Using Adaptive Query Execution
```properties
# ❌ Missing performance optimizations
spark.sql.adaptive.enabled=false

# ✅ Enable AQE for automatic optimizations
spark.sql.adaptive.enabled=true
spark.sql.adaptive.coalescePartitions.enabled=true
```

## Key Takeaways

1. **Start Simple**: Begin with basic configurations and tune incrementally
2. **Monitor First**: Always monitor before and after configuration changes  
3. **Test Thoroughly**: Test configuration changes in development environment
4. **Document Changes**: Keep track of what configurations work for different workloads
5. **Resource Planning**: Calculate resource needs based on data size and SLA requirements
6. **Use AQE**: Enable Adaptive Query Execution for automatic optimizations
