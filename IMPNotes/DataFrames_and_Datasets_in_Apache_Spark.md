# DataFrames and Datasets in Apache Spark

## DataFrames

### What are DataFrames?
- **Distributed table-like collection** of rows with named columns
- Built on top of RDDs with additional optimizations through **Catalyst optimizer**
- **Immutable** like RDDs but with schema information
- Higher-level abstraction that provides better performance than raw RDDs

### Key Characteristics
- **Schema awareness**: Each column has a name and data type
- **Catalyst optimization**: Automatic query optimization
- **Language support**: Available in Scala, Java, Python, and R
- **SQL compatibility**: Can be queried using SQL syntax

### Benefits over RDDs
| Feature | RDDs | DataFrames |
|---------|------|------------|
| Schema | No schema info | Rich schema information |
| Optimization | Manual optimization | Automatic via Catalyst |
| API | Low-level, functional | High-level, declarative |
| Performance | Good | Better (optimized) |
| Debugging | Complex | Easier with schema |

### Creating DataFrames
```scala
// From JSON file
val df = spark.read.json("path/to/file.json")

// From Parquet
val df = spark.read.parquet("path/to/file.parquet")

// From RDD
val df = rdd.toDF("col1", "col2", "col3")

// Programmatically
import org.apache.spark.sql.types._
val schema = StructType(Array(
  StructField("name", StringType, true),
  StructField("age", IntegerType, true)
))
val df = spark.createDataFrame(rdd, schema)
```

### Common DataFrame Operations
```scala
// Selection
df.select("name", "age")
df.select($"name", $"age" + 1)

// Filtering
df.filter($"age" > 25)
df.where("age > 25")

// Grouping
df.groupBy("department").count()
df.groupBy("department").agg(avg("salary"), max("age"))

// Joining
df1.join(df2, "common_column")
df1.join(df2, df1("id") === df2("user_id"), "left")
```

## Datasets

### What are Datasets?
- **Type-safe** version of DataFrames (Scala and Java only)
- Combine the **benefits of RDDs** (type safety) with **DataFrame optimizations**
- Compile-time type checking with runtime optimization
- Dataset[Row] is equivalent to DataFrame

### Key Features
- **Compile-time type safety**: Catch errors at compile time
- **Catalyst optimization**: Same optimizations as DataFrames
- **Encoder-based serialization**: Efficient serialization without Java serialization overhead
- **Object-oriented programming**: Work with strongly-typed objects

### Creating Datasets
```scala
// Case class definition
case class Person(name: String, age: Int, city: String)

// From sequence
val ds = Seq(Person("John", 25, "NYC"), Person("Jane", 30, "LA")).toDS()

// From DataFrame
val ds = df.as[Person]

// From file with automatic inference
val ds = spark.read.json("people.json").as[Person]
```

### Dataset Operations
```scala
// Type-safe operations
ds.filter(_.age > 25)
ds.map(_.name.toUpperCase)
ds.groupByKey(_.city).count()

// SQL-like operations (still available)
ds.select("name", "age")
ds.where("age > 25")
```

## DataFrame vs Dataset vs RDD Comparison

| Aspect | RDD | DataFrame | Dataset |
|--------|-----|-----------|---------|
| **Type Safety** | Compile-time | Runtime | Compile-time |
| **Schema** | No | Yes | Yes |
| **Optimization** | None | Catalyst | Catalyst |
| **Serialization** | Java/Kryo | Tungsten | Encoder-based |
| **Language Support** | Scala, Java, Python | All languages | Scala, Java only |
| **Performance** | Good | Better | Best |
| **Memory Usage** | Higher | Lower | Lowest |
| **Learning Curve** | Steep | Moderate | Moderate |

## When to Use What?

### Use RDDs when:
- You need low-level control over data distribution
- Working with unstructured data
- Performing complex data transformations that don't fit SQL paradigm
- Using languages other than Scala/Java and need type safety

### Use DataFrames when:
- Working with structured or semi-structured data
- Need high-level operations and SQL queries
- Want automatic optimization
- Using Python or R
- Performance is critical

### Use Datasets when:
- Need compile-time type safety (Scala/Java)
- Want to combine functional programming with SQL optimizations
- Working with domain objects
- Need both performance and type safety

## Best Practices

### DataFrame Best Practices
1. **Use built-in functions** instead of UDFs when possible
2. **Cache frequently used DataFrames** with appropriate storage levels
3. **Use column pruning** - select only needed columns early
4. **Predicate pushdown** - filter data as early as possible
5. **Avoid collect()** on large datasets - use actions like `count()`, `take()`

### Dataset Best Practices
1. **Use case classes** for complex data structures
2. **Leverage encoders** for custom types when needed
3. **Mix typed and untyped operations** judiciously
4. **Use Dataset APIs** for compile-time safety in critical paths

### Common Patterns
```scala
// Efficient column selection
df.select("col1", "col2").filter($"col1" > 100)

// Proper caching
val processed = df.filter(...).select(...)
processed.cache()
// Use processed multiple times
processed.unpersist()

// Safe type conversion
val ds = df.as[Person] // Will fail at runtime if schema doesn't match
```

## Schema Operations

### Schema Inspection
```scala
// Print schema
df.printSchema()

// Get schema programmatically
val schema = df.schema
schema.fields.foreach(field => println(s"${field.name}: ${field.dataType}"))
```

### Schema Evolution
```scala
// Add column
val newDf = df.withColumn("new_col", lit("default_value"))

// Rename column
val renamedDf = df.withColumnRenamed("old_name", "new_name")

// Change column type
val typedDf = df.withColumn("age", $"age".cast(StringType))
```

## Performance Considerations

### DataFrame/Dataset Optimizations
- **Predicate pushdown**: Filters are pushed to data sources
- **Column pruning**: Only required columns are read
- **Constant folding**: Constants are pre-computed
- **Join reordering**: Joins are reordered for efficiency
- **Broadcast join optimization**: Small tables are broadcast automatically

### Memory Management
- DataFrames use **Tungsten's binary format** for memory efficiency
- **Off-heap storage** reduces GC pressure
- **Code generation** eliminates virtual function calls
- **Vectorized execution** processes multiple rows together
