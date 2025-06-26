# Apache Spark Fundamentals

## What is Apache Spark?
Apache Spark is a **distributed data processing engine** designed for fast computation on large datasets. It uses **in-memory computing** and **distributed computing** for speed and is not a storage system, messaging system, or database engine.

## Key Characteristics
- **Fast**: In-memory processing capabilities
- **Distributed**: Runs across clusters of machines  
- **Fault-tolerant**: Can recover from failures automatically
- **Unified**: Supports batch processing, streaming, ML, and graph processing

## Core Architecture
Spark operates on a master-worker architecture where:
- **Driver Program**: Coordinates the execution
- **Cluster Manager**: Manages resources
- **Executors**: Run tasks on worker nodes

## Why Choose Spark?
- 100x faster than Hadoop MapReduce for in-memory operations
- Easy-to-use APIs in multiple languages (Scala, Java, Python, R)
- Built-in libraries for SQL, streaming, machine learning, and graph processing
- Can run on various cluster managers (YARN, Mesos, Kubernetes)
