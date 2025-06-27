# Spark Deployment Modes and Cluster Managers

## Overview
Apache Spark can run in different deployment modes and on various cluster managers. Understanding these options is crucial for choosing the right deployment strategy for your use case.

## Deployment Modes

### 1. Client Mode vs Cluster Mode

| Aspect | Client Mode | Cluster Mode |
|--------|-------------|--------------|
| **Driver Location** | On client machine | On cluster node |
| **Network Dependency** | Driver must stay connected | Driver runs independently |
| **Failure Impact** | Client failure = job failure | More fault tolerant |
| **Resource Usage** | Uses client resources | Uses cluster resources |
| **Best For** | Interactive jobs, development | Production, long-running jobs |

### Client Mode
```bash
spark-submit \
  --master yarn \
  --deploy-mode client \
  --executor-memory 4g \
  --executor-cores 2 \
  myapp.jar
```

**Characteristics:**
- Driver runs on the machine that submitted the job
- Client machine must stay connected during job execution
- Good for interactive analysis (Spark Shell, Jupyter notebooks)
- Driver logs visible on client machine

### Cluster Mode  
```bash
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --executor-memory 4g \
  --executor-cores 2 \
  myapp.jar
```

**Characteristics:**
- Driver runs on a cluster node (not client)
- Client can disconnect after submission
- Better fault tolerance
- Preferred for production jobs

## Cluster Managers

### 1. Local Mode

#### Single-threaded Local
```bash
spark-submit --master local myapp.jar
```

#### Multi-threaded Local
```bash
# Use all available cores
spark-submit --master local[*] myapp.jar

# Use specific number of cores
spark-submit --master local[4] myapp.jar
```

**Use Cases:**
- Development and testing
- Small datasets
- Debugging applications
- Learning Spark concepts

### 2. Standalone Cluster

#### Architecture
```
Master Node (Spark Master)
├── Worker Node 1 (Spark Worker)
├── Worker Node 2 (Spark Worker)  
└── Worker Node N (Spark Worker)
```

#### Starting Standalone Cluster
```bash
# Start master
$SPARK_HOME/sbin/start-master.sh

# Start workers
$SPARK_HOME/sbin/start-worker.sh spark://master-host:7077

# Or start all
$SPARK_HOME/sbin/start-all.sh
```

#### Submitting to Standalone
```bash
spark-submit \
  --master spark://master-host:7077 \
  --executor-memory 2g \
  --total-executor-cores 8 \
  myapp.jar
```

**Characteristics:**
- Simple to set up and manage
- Built-in web UI for monitoring
- Good for dedicated Spark clusters
- Manual resource management

### 3. YARN (Yet Another Resource Negotiator)

#### YARN Architecture with Spark
```
ResourceManager (YARN Master)
├── NodeManager 1
│   └── Container (Spark Executor)
├── NodeManager 2  
│   ├── Container (Spark Driver - cluster mode)
│   └── Container (Spark Executor)
└── NodeManager N
    └── Container (Spark Executor)
```

#### YARN Client Mode
```bash
spark-submit \
  --master yarn \
  --deploy-mode client \
  --executor-memory 4g \
  --num-executors 10 \
  myapp.jar
```

#### YARN Cluster Mode
```bash
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --executor-memory 4g \
  --num-executors 10 \
  myapp.jar
```

#### YARN Configuration
```properties
# spark-defaults.conf for YARN
spark.master=yarn
spark.submit.deployMode=cluster
spark.executor.memory=4g
spark.executor.cores=2
spark.dynamicAllocation.enabled=true
spark.shuffle.service.enabled=true
```

**Advantages:**
- Integrates with Hadoop ecosystem
- Dynamic resource allocation
- Multi-tenancy support
- Resource queues and priorities
- Comprehensive monitoring

### 4. Kubernetes

#### Kubernetes Architecture
```
Kubernetes Cluster
├── Driver Pod
├── Executor Pod 1
├── Executor Pod 2
└── Executor Pod N
```

#### Submitting to Kubernetes
```bash
spark-submit \
  --master k8s://https://kubernetes-api-server:443 \
  --deploy-mode cluster \
  --conf spark.executor.instances=3 \
  --conf spark.kubernetes.container.image=spark:latest \
  --conf spark.kubernetes.driver.pod.name=spark-driver \
  local:///path/to/myapp.jar
```

#### Kubernetes Configuration
```yaml
# spark-operator example
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: spark-pi
spec:
  type: Scala
  mode: cluster
  image: gcr.io/spark-operator/spark:v3.1.1
  mainClass: org.apache.spark.examples.SparkPi
  mainApplicationFile: local:///opt/spark/examples/jars/spark-examples.jar
  driver:
    cores: 1
    memory: 1g
  executor:
    cores: 1
    instances: 2
    memory: 1g
```

**Advantages:**
- Container-based deployment
- Auto-scaling capabilities
- Integration with cloud-native tools
- Resource isolation
- Modern orchestration features

### 5. Mesos (Deprecated)

Mesos support has been deprecated in Spark 3.2+, but understanding its concepts helps with other cluster managers.

**Note**: Mesos was removed due to low adoption and maintenance overhead. Consider YARN or Kubernetes instead.

## Cluster Manager Comparison

| Feature | Local | Standalone | YARN | Kubernetes |
|---------|-------|------------|------|------------|
| **Setup Complexity** | None | Low | Medium | Medium |
| **Scalability** | Single machine | High | Very High | Very High |
| **Resource Sharing** | N/A | Limited | Excellent | Excellent |
| **Fault Tolerance** | None | Basic | High | High |
| **Multi-tenancy** | No | Limited | Yes | Yes |
| **Dynamic Allocation** | No | No | Yes | Yes |
| **Monitoring** | Limited | Basic | Comprehensive | Comprehensive |
| **Best For** | Development | Dedicated clusters | Hadoop ecosystems | Cloud-native |

## Resource Allocation Strategies

### 1. Static Allocation
```bash
spark-submit \
  --master yarn \
  --executor-memory 4g \
  --executor-cores 2 \
  --num-executors 10 \
  myapp.jar
```

**Characteristics:**
- Fixed number of executors
- Resources reserved throughout job
- Predictable performance
- May waste resources during idle periods

### 2. Dynamic Allocation

#### Configuration
```properties
spark.dynamicAllocation.enabled=true
spark.dynamicAllocation.minExecutors=1
spark.dynamicAllocation.maxExecutors=20
spark.dynamicAllocation.initialExecutors=5

# Scaling behavior
spark.dynamicAllocation.executorIdleTimeout=60s
spark.dynamicAllocation.schedulerBacklogTimeout=1s
```

#### Requirements
```properties
# Required for dynamic allocation
spark.shuffle.service.enabled=true

# For YARN
spark.dynamicAllocation.shuffleTracking.enabled=true
```

**Advantages:**
- Efficient resource utilization
- Automatic scaling based on workload
- Cost optimization in cloud environments
- Better cluster resource sharing

## Deployment Strategies by Environment

### 1. Development Environment
```bash
# Local mode for development
spark-shell --master local[*]

# Small standalone cluster for integration testing
spark-submit --master spark://dev-master:7077 myapp.jar
```

### 2. Staging Environment
```bash
# YARN client mode for debugging
spark-submit \
  --master yarn \
  --deploy-mode client \
  --executor-memory 2g \
  myapp.jar
```

### 3. Production Environment
```bash  
# YARN cluster mode for production
spark-submit \
  --master yarn \
  --deploy-mode cluster \
  --executor-memory 8g \
  --num-executors 20 \
  --conf spark.dynamicAllocation.enabled=true \
  myapp.jar
```

### 4. Cloud Environment
```bash
# Kubernetes with auto-scaling
spark-submit \
  --master k8s://https://k8s-api:443 \
  --deploy-mode cluster \
  --conf spark.kubernetes.container.image=myapp:latest \
  --conf spark.executor.instances=5 \
  --conf spark.dynamicAllocation.enabled=true \
  local:///opt/spark/myapp.jar
```

## Monitoring and Management

### 1. Spark Web UI Ports

| Cluster Manager | Driver UI | Master UI | Worker UI |
|----------------|-----------|-----------|-----------|
| Local | 4040 | N/A | N/A |
| Standalone | 4040 | 8080 | 8081 |
| YARN | 4040 | ResourceManager UI | NodeManager UI |
| Kubernetes | 4040 | Kubernetes Dashboard | Pod logs |

### 2. Application Monitoring
```bash
# Check YARN applications
yarn application -list

# Check Kubernetes pods
kubectl get pods -l spark-role=executor

# Standalone cluster status
curl http://master:8080/json/
```

### 3. Log Management

#### Local Mode
```bash
