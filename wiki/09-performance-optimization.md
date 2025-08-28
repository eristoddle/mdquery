# Performance Optimization

## Overview

mdquery is designed for high performance even with large collections of markdown files. This section covers performance optimization strategies, caching mechanisms, and best practices for optimal performance.

## Caching Mechanisms

### File System Cache

mdquery implements a comprehensive caching system to avoid redundant processing:

#### Cache Types

1. **File Content Cache**: Stores parsed file content
2. **Metadata Cache**: Caches extracted metadata
3. **Query Result Cache**: Caches frequently used query results
4. **Index Cache**: Caches directory scanning results

#### Cache Configuration

```json
{
  "cache": {
    "enabled": true,
    "type": "file",
    "directory": ".mdquery/cache",
    "max_size_mb": 100,
    "ttl_hours": 24,
    "compress": true,
    "cleanup_on_start": false,
    "cache_policies": {
      "file_content": "modified_time",
      "metadata": "content_hash",
      "query_results": "ttl",
      "index": "directory_mtime"
    }
  }
}
```

#### Cache API Usage

```python
from mdquery.cache import CacheManager

# Initialize cache manager
cache_manager = CacheManager(cache_dir=".mdquery/cache")

# Enable cache for indexer
indexer = Indexer(db_manager, cache_manager=cache_manager)

# Cache will automatically be used for:
# - File content parsing
# - Metadata extraction
# - Directory scanning
```

### Query Result Caching

Query results are automatically cached based on query hash and parameters:

```python
# First execution - hits database
result1 = query_engine.execute_query("SELECT * FROM files WHERE tags LIKE '%research%'")

# Second execution - served from cache
result2 = query_engine.execute_query("SELECT * FROM files WHERE tags LIKE '%research%'")
```

#### Cache Invalidation

Cache is automatically invalidated when:
- Files are modified or added
- Database schema changes
- Cache TTL expires
- Manual cache clearing

```python
# Manual cache clearing
cache_manager.clear_cache()
cache_manager.clear_query_cache()
cache_manager.clear_file_cache("specific_file.md")
```

## Indexing Strategies

### Incremental Indexing

Incremental indexing processes only changed files:

```python
# Only processes new or modified files
result = indexer.incremental_index_directory("/path/to/notes")
print(f"Processed: {result.files_processed}")
print(f"Skipped: {result.files_skipped}")
```

#### How Incremental Indexing Works

1. **File Modification Check**: Compares file `mtime` with database records
2. **Content Hash Verification**: Uses SHA-256 hash to detect content changes
3. **Selective Processing**: Only parses changed files
4. **Dependency Tracking**: Updates related records when files change

### Parallel Processing

Enable parallel processing for large repositories:

```json
{
  "index": {
    "parallel_processing": true,
    "max_workers": 4,
    "chunk_size": 100
  }
}
```

```python
# Parallel indexing
indexer = Indexer(db_manager, max_workers=4, chunk_size=100)
result = indexer.index_directory("/path/to/large/repository")
```

### Batch Operations

Process files in batches for memory efficiency:

```python
# Configure batch size
indexer.set_batch_size(50)  # Process 50 files per batch

# Large repository indexing with batching
result = indexer.index_directory("/path/to/huge/repository", batch_mode=True)
```

## Database Optimization

### SQLite Configuration

Optimize SQLite for better performance:

```json
{
  "database": {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": 10000,
    "temp_store": "MEMORY",
    "mmap_size": 268435456,
    "optimize_on_close": true,
    "vacuum_on_start": false
  }
}
```

### Index Optimization

mdquery automatically creates database indexes for optimal query performance:

```sql
-- Automatically created indexes
CREATE INDEX idx_files_modified_date ON files(modified_date);
CREATE INDEX idx_files_directory ON files(directory);
CREATE INDEX idx_tags_tag ON tags(tag);
CREATE INDEX idx_tags_file_id ON tags(file_id);
CREATE INDEX idx_links_file_id ON links(file_id);
CREATE INDEX idx_frontmatter_key ON frontmatter(key);
CREATE INDEX idx_frontmatter_file_id ON frontmatter(file_id);
```

### FTS5 Optimization

Full-text search is optimized using SQLite FTS5:

```sql
-- FTS5 table with optimal configuration
CREATE VIRTUAL TABLE content_fts USING fts5(
  title, content, headings,
  content='files',
  content_rowid='id',
  tokenize='porter ascii'
);
```

#### FTS5 Best Practices

1. **Use MATCH for text searches** instead of LIKE
2. **Optimize queries** with specific field searches
3. **Use relevance ranking** for better results

```sql
-- Optimized: Uses FTS5 MATCH
SELECT filename FROM files WHERE content MATCH 'python tutorial';

-- Not optimized: Uses LIKE on full content
SELECT filename FROM files WHERE content LIKE '%python tutorial%';
```

### Query Optimization

#### Automatic Query Optimization

mdquery includes a `PerformanceOptimizer` that automatically optimizes queries:

```python
from mdquery.performance import PerformanceOptimizer

optimizer = PerformanceOptimizer()

# Original query
original_sql = "SELECT * FROM files WHERE content LIKE '%python%'"

# Optimized query
optimized_sql = optimizer.optimize_query(original_sql)
# Result: "SELECT * FROM files WHERE content MATCH 'python' LIMIT 1000"
```

#### Optimization Rules

The optimizer applies these rules automatically:

1. **Replace LIKE with MATCH**: For content searches
2. **Add LIMIT clauses**: Prevent large result sets
3. **Use IN instead of multiple OR**: For better performance
4. **Push WHERE conditions**: Into JOINs where possible
5. **Use EXISTS instead of IN**: For subqueries

#### Manual Query Optimization

```sql
-- Instead of this (slow)
SELECT f.filename FROM files f
WHERE f.id IN (
  SELECT t.file_id FROM tags t WHERE t.tag = 'research'
);

-- Use this (fast)
SELECT f.filename FROM files f
WHERE EXISTS (
  SELECT 1 FROM tags t WHERE t.file_id = f.id AND t.tag = 'research'
);
```

## Performance Monitoring

### Built-in Performance Metrics

mdquery tracks performance metrics automatically:

```python
# Get performance statistics
stats = query_engine.get_performance_stats()
print(f"Average query time: {stats.avg_query_time:.3f}s")
print(f"Cache hit rate: {stats.cache_hit_rate:.2%}")
print(f"Total queries: {stats.total_queries}")
```

### Performance Profiling

Enable detailed performance profiling:

```python
from mdquery.performance import PerformanceProfiler

# Enable profiling
profiler = PerformanceProfiler()
query_engine.set_profiler(profiler)

# Execute queries
result = query_engine.execute_query("SELECT * FROM files")

# Get profiling results
profile = profiler.get_profile()
print(f"Query parsing: {profile.parse_time:.3f}s")
print(f"Database execution: {profile.db_time:.3f}s")
print(f"Result formatting: {profile.format_time:.3f}s")
```

### Memory Usage Monitoring

Monitor memory usage during operations:

```python
from mdquery.performance import MemoryMonitor

monitor = MemoryMonitor()

# Monitor indexing
monitor.start()
result = indexer.index_directory("/path/to/notes")
stats = monitor.stop()

print(f"Peak memory usage: {stats.peak_memory_mb:.1f} MB")
print(f"Memory delta: {stats.memory_delta_mb:.1f} MB")
```

## Performance Best Practices

### Indexing Best Practices

1. **Use incremental indexing** for regular updates
2. **Enable parallel processing** for large repositories
3. **Configure appropriate batch sizes** based on available memory
4. **Use file exclusion patterns** to skip unnecessary files
5. **Schedule indexing** during off-peak hours for large repositories

```python
# Optimal indexing configuration
config = {
    "incremental": True,
    "parallel_processing": True,
    "max_workers": min(4, os.cpu_count()),
    "batch_size": 100,
    "exclude_patterns": [".git", "node_modules", ".obsidian", "*.tmp"]
}
```

### Query Best Practices

1. **Use LIMIT clauses** to prevent large result sets
2. **Use FTS5 MATCH** for content searches
3. **Index frequently queried columns**
4. **Use EXISTS instead of IN** for subqueries
5. **Cache frequently used queries**

```sql
-- Good query patterns
SELECT filename, modified_date
FROM files
WHERE modified_date > '2024-01-01'
ORDER BY modified_date DESC
LIMIT 20;

SELECT filename
FROM files
WHERE content MATCH 'python programming'
LIMIT 50;

SELECT f.filename
FROM files f
WHERE EXISTS (
    SELECT 1 FROM tags t
    WHERE t.file_id = f.id AND t.tag = 'important'
)
LIMIT 100;
```

### Configuration Best Practices

1. **Enable caching** for repeated operations
2. **Configure appropriate cache sizes** based on available disk space
3. **Use WAL mode** for better concurrent access
4. **Set appropriate timeouts** for query operations
5. **Optimize database settings** for your use case

```json
{
  "cache": {
    "enabled": true,
    "max_size_mb": 500,
    "ttl_hours": 24
  },
  "database": {
    "journal_mode": "WAL",
    "cache_size": 10000,
    "temp_store": "MEMORY"
  },
  "query": {
    "timeout": 30,
    "default_limit": 1000,
    "enable_optimization": true
  }
}
```

## Troubleshooting Performance Issues

### Common Performance Problems

1. **Slow queries**: Usually caused by missing indexes or inefficient SQL
2. **High memory usage**: Often due to large result sets or disabled caching
3. **Slow indexing**: Typically caused by large files or disabled parallel processing
4. **Cache misses**: Usually due to frequently changing files or incorrect cache configuration

### Performance Debugging

#### Query Performance Analysis

```python
# Analyze slow queries
slow_queries = query_engine.get_slow_queries(threshold=1.0)  # > 1 second
for query_info in slow_queries:
    print(f"Query: {query_info.sql}")
    print(f"Time: {query_info.execution_time:.3f}s")
    print(f"Rows: {query_info.row_count}")
    print("---")
```

#### Cache Performance Analysis

```python
# Analyze cache performance
cache_stats = cache_manager.get_statistics()
print(f"Cache hit rate: {cache_stats.hit_rate:.2%}")
print(f"Cache size: {cache_stats.size_mb:.1f} MB")
print(f"Eviction count: {cache_stats.evictions}")
```

#### Memory Usage Analysis

```python
# Check memory usage
memory_stats = query_engine.get_memory_stats()
print(f"Current memory: {memory_stats.current_mb:.1f} MB")
print(f"Peak memory: {memory_stats.peak_mb:.1f} MB")
print(f"Database memory: {memory_stats.db_cache_mb:.1f} MB")
```

### Performance Optimization Workflow

1. **Profile the operation** to identify bottlenecks
2. **Analyze query patterns** for optimization opportunities
3. **Check cache effectiveness** and adjust configuration
4. **Monitor memory usage** and optimize batch sizes
5. **Verify database indexes** are being used effectively
6. **Test changes** with performance benchmarks

```python
# Complete performance optimization workflow
def optimize_performance():
    # 1. Profile current performance
    profiler = PerformanceProfiler()
    query_engine.set_profiler(profiler)

    # 2. Run representative workload
    run_benchmark_queries()

    # 3. Analyze results
    profile = profiler.get_profile()
    identify_bottlenecks(profile)

    # 4. Apply optimizations
    apply_optimizations()

    # 5. Re-test and compare
    new_profile = run_benchmark_again()
    compare_performance(profile, new_profile)
```