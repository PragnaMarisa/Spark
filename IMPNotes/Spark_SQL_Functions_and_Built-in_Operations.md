# Spark SQL Functions and Built-in Operations

## Overview
Spark SQL provides a rich set of built-in functions for data manipulation, transformation, and analysis. These functions are optimized by the Catalyst optimizer and can be used with DataFrames and SQL queries.

## Function Categories

### 1. Column Functions
```scala
import org.apache.spark.sql.functions._

// Basic column operations
df.select(col("name"), upper(col("name")))
df.select($"age" + 1)
df.select(when($"age" > 18, "Adult").otherwise("Minor"))
```

### 2. String Functions
| Function | Purpose | Example |
|----------|---------|---------|
| `upper()`, `lower()` | Case conversion | `df.select(upper($"name"))` |
| `length()` | String length | `df.select(length($"description"))` |
| `concat()` | String concatenation | `df.select(concat($"first", lit(" "), $"last"))` |
| `substring()` | Extract substring | `df.select(substring($"name", 1, 3))` |
| `regexp_replace()` | Regex replacement | `df.select(regexp_replace($"phone", "-", ""))` |
| `split()` | Split string | `df.select(split($"name", " "))` |

### 3. Date and Time Functions
```scala
// Current date/time
df.select(current_date(), current_timestamp())

// Date arithmetic
df.select(date_add($"date", 7))  // Add 7 days
df.select(datediff($"end_date", $"start_date"))

// Date formatting
df.select(date_format($"timestamp", "yyyy-MM-dd"))

// Extract components
df.select(year($"date"), month($"date"), dayofweek($"date"))
```

### 4. Mathematical Functions
```scala
// Basic math
df.select(abs($"value"), round($"price", 2))

// Trigonometric
df.select(sin($"angle"), cos($"angle"), tan($"angle"))

// Statistical
df.select(sqrt($"value"), pow($"base", $"exponent"))
```

### 5. Aggregate Functions
```scala
// Basic aggregations
df.agg(
  sum($"amount"),
  avg($"price"),
  min($"date"),
  max($"score"),
  count($"id")
)

// Advanced aggregations
df.agg(
  stddev($"values"),
  variance($"scores"),
  collect_list($"items"),
  collect_set($"categories")
)
```

### 6. Window Functions
```scala
import org.apache.spark.sql.expressions.Window

val windowSpec = Window.partitionBy($"department").orderBy($"salary".desc)

df.select(
  $"*",
  row_number().over(windowSpec),
  rank().over(windowSpec),
  dense_rank().over(windowSpec),
  lag($"salary", 1).over(windowSpec),
  lead($"salary", 1).over(windowSpec)
)
```

### 7. Array and Map Functions
```scala
// Array functions
df.select(
  array_contains($"tags", "spark"),
  explode($"items"),
  size($"array_column"),
  sort_array($"numbers")
)

// Map functions
df.select(
  map_keys($"metadata"),
  map_values($"metadata"),
  explode($"map_column")
)
```

### 8. JSON Functions
```scala
// JSON parsing
df.select(
  get_json_object($"json_col", "$.field"),
  json_tuple($"json_col", "field1", "field2")
)

// JSON creation
df.select(to_json(struct($"col1", $"col2")))
```

## User Defined Functions (UDFs)

### Creating UDFs
```scala
// Define UDF
val upperUDF = udf((s: String) => s.toUpperCase)

// Register UDF for SQL
spark.udf.register("upperUDF", upperUDF)

// Use in DataFrame
df.select(upperUDF($"name"))

// Use in SQL
spark.sql("SELECT upperUDF(name) FROM table")
```

### UDF Best Practices
- **Performance**: UDFs are slower than built-in functions
- **Null Safety**: Always handle null values
- **Type Safety**: Use proper Scala/Java types
- **Catalyst**: Built-in functions get optimized, UDFs don't

```scala
// Good UDF with null handling
val safeUDF = udf((s: String) => {
  if (s != null) s.toUpperCase else null
})
```

## Function Performance Tips

### 1. Prefer Built-in Functions
```scala
// ❌ Slower - UDF
val customLength = udf((s: String) => s.length)
df.select(customLength($"name"))

// ✅ Faster - Built-in
df.select(length($"name"))
```

### 2. Use Catalyst-Optimized Operations
```scala
// ✅ Optimized by Catalyst
df.filter($"age" > 18)
df.select(when($"status" === "active", 1).otherwise(0))

// ❌ Not optimized
df.filter(udf_check_age($"age"))
```

### 3. Column Expressions vs UDFs
```scala
// ✅ Column expression - optimized
df.select(
  when($"amount" > 1000, "High")
  .when($"amount" > 500, "Medium")
  .otherwise("Low")
)

// ❌ UDF - not optimized
val categorize = udf((amount: Double) => {
  if (amount > 1000) "High"
  else if (amount > 500) "Medium"
  else "Low"
})
```

## Common Patterns

### 1. Conditional Logic
```scala
// Multiple conditions
df.select(
  when($"age" < 18, "Minor")
  .when($"age" < 65, "Adult")
  .otherwise("Senior")
  .alias("category")
)
```

### 2. Data Cleaning
```scala
df.select(
  // Remove whitespace
  trim($"name"),
  
  // Handle nulls
  coalesce($"phone", lit("N/A")),
  
  // Standardize case
  upper($"state"),
  
  // Extract numbers
  regexp_extract($"text", "\\d+", 0)
)
```

### 3. Data Transformation
```scala
df.select(
  // Parse dates
  to_date($"date_string", "yyyy-MM-dd"),
  
  // Convert types
  $"amount".cast("double"),
  
  // Create arrays
  split($"tags", ","),
  
  // JSON parsing
  get_json_object($"metadata", "$.version")
)
```

## SQL vs DataFrame API

### Same Function, Different Syntax
```scala
// DataFrame API
df.select(upper($"name"), length($"description"))

// SQL
spark.sql("SELECT UPPER(name), LENGTH(description) FROM table")
```

### Mixing Both Approaches
```scala
// Register DataFrame as temp view
df.createOrReplaceTempView("data")

// Use SQL with complex logic
val result = spark.sql("""
  SELECT 
    name,
    CASE 
      WHEN age < 18 THEN 'Minor'
      WHEN age < 65 THEN 'Adult'
      ELSE 'Senior'
    END as category
  FROM data
""")
```

## Function Chaining and Readability

### Method Chaining
```scala
df.select(
  $"name",
  trim(upper($"name")).alias("clean_name"),
  date_format(current_date(), "yyyy-MM-dd").alias("today")
)
```

### Complex Transformations
```scala
val processedDF = df
  .select(
    $"id",
    regexp_replace(trim(lower($"email")), "\\s+", "").alias("clean_email"),
    when(length($"phone") === 10, 
         concat(lit("("), substring($"phone", 1, 3), lit(") "),
                substring($"phone", 4, 3), lit("-"),
                substring($"phone", 7, 4))
    ).otherwise($"phone").alias("formatted_phone")
  )
```

## Key Takeaways

1. **Use Built-in Functions**: Always prefer built-in functions over UDFs for performance
2. **Catalyst Optimization**: Built-in functions are optimized by Catalyst optimizer
3. **Null Handling**: Always consider null values in your transformations
4. **Type Safety**: Use appropriate data types for better performance
5. **Readability**: Chain functions logically and use meaningful aliases
6. **SQL Compatibility**: Most functions work in both DataFrame API and SQL
