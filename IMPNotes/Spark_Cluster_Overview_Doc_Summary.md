# Apache Spark Cluster Execution: Concepts \& Architecture

## 1. SparkContext \& Cluster Managers

**SparkContext** is the starting point for any Spark application. It connects to a **Cluster Manager** to request resources and coordinate computations.

### Types of Cluster Managers

- **Standalone:** Spark's own built-in cluster manager.
- **YARN (Yet Another Resource Negotiator):** Common in Hadoop ecosystems.
- **Kubernetes:** Orchestrates Spark jobs in containers, managed as Pods.

> *Think of the cluster manager as a scheduler that determines where and how your Spark job runs across multiple machines.*

## 2. Executors on Worker Nodes

Once SparkContext connects to the cluster manager:

- **Requests resources** for your application.
- **Cluster manager allocates worker nodes** (physical/virtual machines).
- **Executors** (JVM/Python processes) are launched on these nodes.

**Executors**:

- Run your Spark computation (map, reduce, filter, etc.)
- Store data required by the app (such as cached or intermediate results)


## 3. Application Code Distribution

- Your Spark app (Python, Scala, Java, etc.) is packaged as a **JAR** or **Python file**.
- The code is sent from the **driver** (your machine or gateway node) to the **executors**.
- Spark automatically ships any lambdas or functions you define.

**Example:**

```python
data = sc.textFile("hdfs://myfile.txt")
filtered = data.filter(lambda line: "error" in line)
count = filtered.count()
```

*The lambda inside filter is shipped to each executor, to run on each partition.*

## 4. Tasks \& Execution Workflow

- SparkContext **divides the job into tasks** (units of work, e.g., processing a partition).
- **Tasks are grouped into stages**, and all stages together form the job.
- For example, a file split into 10 partitions generates 10 tasks run in parallel across executors.


### Summary Flow

```
You (Driver Program)
        │
      SparkContext
        │
   Cluster Manager
     (e.g., YARN)
        │
     Executors
        │
      Tasks
```

*You → SparkContext → Cluster Manager → Executors → Tasks*

## 5. Real-World Analogy

If your Spark job is like a company project:

- **Driver:** You, the project manager.
- **SparkContext:** Your manager, organizing the project.
- **Cluster Manager:** Staffing agency, finding available workers.
- **Worker Nodes:** Office buildings.
- **Executors:** Employees in those offices.
- **Tasks:** Individual assignments in the company project.


## 6. Pods in Kubernetes

When running Spark on Kubernetes:

### What is a Pod?

- The **smallest deployable unit** in Kubernetes.
- Wraps one or more containers (usually Docker).
- Containers in a Pod:
    - Run together on the same node.
    - Share the same storage and network.
    - Are scheduled as a unit.

**Use Case in Spark:**

- Spark **driver** and **executors** each run in their own Pod.
- Kubernetes schedules each Pod on available nodes.
- Pods run tasks, then terminate when the job ends.


### Pod Example (YAML)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
spec:
  containers:
    - name: app-container
      image: my-app-image:v1
    - name: logging-sidecar
      image: log-agent:v1
```


## 7. Worker Nodes in Spark

- **Worker node:** A machine in the cluster that hosts executors.
- Can run one or more executors depending on available CPU and RAM.

Diagram:

```
+------------------+
|   Driver Program |
+------------------+
         |
         v
+---------------------+
|  Cluster Manager    |
+---------------------+
         |
         v
+-----------------+   +-----------------+
|  Worker Node 1  |   |  Worker Node 2  |
+-----------------+   +-----------------+
|  Executor(s)    |   |  Executor(s)    |
+-----------------+   +-----------------+
```


## 8. Executors per Worker Node

- Each **worker node** can have **multiple executors**, controlled by config \& available hardware.


### Example

If a node has **16 cores** and **64 GB RAM** and you run:

- `--executor-cores 4`
- `--executor-memory 8G`

Then:

- CPU limit: 16 / 4 = 4 executors
- RAM limit: 64 / 8 = 8 executors
- Final: 4 executors per node (CPU is limiting)


### Key Configuration Flags

| Config | Meaning |
| :-- | :-- |
| --executor-cores | CPU cores per executor |
| --executor-memory | RAM per executor |
| --num-executors | Total executors (cluster-wide) |
| spark.executor.cores | (same as --executor-cores) |
| spark.executor.instances | (same as --num-executors) |

## 9. Tasks per Executor

- Each executor runs as many parallel tasks as the **number of cores assigned to it**.


### Example

- 3 worker nodes with 8 cores each.
- Run with `--executor-cores 4`.
- Spark assigns **2 executors per node**:
    - Total executors: 6
    - Each executor runs 4 parallel tasks: 6 × 4 = 24 tasks in parallel.


### Configuration Table

| Config | Parallel Tasks per Executor |
| :-- | :-- |
| --executor-cores 1 | 1 task at a time |
| --executor-cores 4 | 4 tasks at a time |
| 10 executors × 4 cores | 40 tasks in parallel total |

## 10. Concept Table: Worker Nodes vs Executors

| Term | Role |
| :-- | :-- |
| Worker Node | Machine in cluster hosting executors |
| Executor | Process on a worker node running Spark tasks |

- **One node, multiple executors:** How many depends on node resources and Spark config.
- **Executor parallelism:** Number of parallel tasks equals number of cores assigned.

---

# 🚀 Apache Spark: Driver, Executors & RPC Explained

---

## 🧠 Overview of Spark Architecture

Apache Spark is a distributed data processing framework. Its core components are:

- **Driver Program**: Coordinates the execution of Spark jobs.
- **Executors**: Run the actual tasks on the worker nodes.
- **Cluster Manager**: Allocates resources to applications.

---

## 🖥️ Spark Driver

### What It Does:
- Schedules tasks across executors.
- Maintains metadata, stages, and job progress.
- Collects results from executors.

### Key Requirements:
- Must be **reachable** from all worker nodes.
- Must be **network addressable** (accessible via IP or hostname).
- Should be **close to executors**, ideally on the **same local network (LAN)**.

### Configuration:
```bash
spark.driver.host=<driver_host>
spark.driver.port=<driver_port>
```

## ⚙️ Spark Executors

### What They Do:
- Run the actual tasks as instructed by the driver.
- Store data in memory or disk for shuffle or caching.
- Communicate with the driver during the job lifecycle.

---

## 📡 Network Requirements

- Executors **initiate connections** to the driver.
- The driver must stay **running and network-accessible** for the full duration of the job.
- If the driver is far from executors (e.g., in another data center), **performance and stability suffer**.

---

## 🌐 Remote Procedure Call (RPC) in Spark

### What is RPC?
> A **Remote Procedure Call (RPC)** lets a program call a function on another machine as if it were local.

### Why RPC Matters in Spark:
If you're submitting jobs from a remote location (e.g., a web UI, script, or another service), **don’t run the driver remotely**.

Instead:
1. Run the **Spark driver near the cluster**.
2. Use **RPC (or HTTP APIs like Livy)** to communicate with the driver remotely.

---

### ✅ Benefits of RPC Approach:

| Without RPC | With RPC |
|-------------|----------|
| Driver is far from executors → High latency | Driver stays near executors |
| Risk of connection issues | Reliable and fast execution |
| Slower scheduling and job performance | Efficient task coordination |

---

## 📦 Tools that Use RPC with Spark

- **Apache Livy**: A REST API for submitting jobs to Spark clusters.
- **Custom RPC Clients**: Apps (e.g., Python, Java, Node.js) that send job definitions to a running driver.

---

## 🧾 Summary Table

| Component | Role | Best Practice |
|----------|------|----------------|
| **Driver** | Coordinates jobs | Run close to workers |
| **Executors** | Run tasks | Connect to driver |
| **RPC** | Remote communication method | Use to control driver remotely |
| **Remote Client** | External system | Talk to driver via RPC/API |

---

## 📌 Key Takeaways

- Spark driver must be **reachable and close** to executors.
- Using **RPC** allows remote systems to **control Spark jobs efficiently**.
- Never run a driver far from worker nodes — use **remote submission methods** instead.

---

