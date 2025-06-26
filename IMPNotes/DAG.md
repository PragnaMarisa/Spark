
# 🔷 DAG in Apache Spark

## 📌 What is a DAG?

A **DAG (Directed Acyclic Graph)** is a **graph of computation** in Spark where:

- **Directed**: Each step points to the next (order matters).  
- **Acyclic**: No step loops back (no cycles).  
- **Graph**: Nodes represent operations or data (like RDDs), and edges represent dependencies.

---

## 🧠 Why DAG in Spark?

- DAG helps Spark **plan** and **optimize** execution.  
- It enables **fault tolerance** via **lineage**.  
- Spark breaks a DAG into **stages** for parallel execution.

---

## 🔗 DAG vs Lineage

| Term        | Description                                              |
|-------------|----------------------------------------------------------|
| **Lineage** | Logical history of how a dataset (RDD/DataFrame) was built |
| **DAG**     | Graph representation of this lineage                     |

✅ Spark **internally represents lineage as a DAG**.

---

## 🔍 Visual Example

```scala
val raw = sc.textFile("logs.txt")
val errors = raw.filter(_.contains("ERROR"))
val timestamps = errors.map(_.split(" ")(0))
timestamps.saveAsTextFile("errors_out")
```

### DAG Representation:

```
textFile("logs.txt")
       ↓
filter (contains "ERROR")
       ↓
map (extract timestamp)
       ↓
saveAsTextFile("errors_out")
```

Each operation forms a **node**, and edges show **data dependencies**.

---

## ⚙️ Execution Flow

1. Transformations like `map`, `filter` build the DAG (**lazy**).
2. Actions like `saveAsTextFile` trigger **job execution**.
3. Spark analyzes the DAG, splits it into **stages**.
4. Each stage runs as a **task set** across the cluster.

---

## 🛡️ Fault Tolerance via DAG

- If a partition fails, Spark **recomputes** it using the **lineage DAG**.  
- No need to persist intermediate results manually.

---

## ✅ Summary

- DAG = **Directed Acyclic Graph** of transformations.  
- It is **Spark's backbone** for execution planning and recovery.  
- Built from **RDD/DataFrame transformations**.  
- Used for **optimizing**, **scheduling**, and **recovering** jobs.
