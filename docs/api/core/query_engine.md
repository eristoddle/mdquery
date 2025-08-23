# QueryEngine API

The QueryEngine executes SQL queries against the indexed markdown data, providing a powerful interface for searching and analyzing your notes.

## Class: `mdquery.query.QueryEngine`

### Constructor

```python
def __init__(self, cache_manager: CacheManager = None)
```

**Parameters:**
- `cache_manager` (CacheManager, optional): Cache manager instance. If None, creates a default instance.

**Example:**
```python
from mdquery import QueryEngine, CacheManager

cache_manager = CacheManager("my_notes.db")
query_engine = QueryEngine(cache_manager=cache_manager)
```

### Methods

#### `execute_query(sql: str) -> QueryResult`

Executes a SQL query against the indexed data.

**Parameters:**
- `sql` (str): SQL query string

**Returns:**
- `QueryResult`: Object containing query results and metadata

**Example:**
```python
result = query_engine.execute_query(
    "SELECT filename, tags FROM files WHERE tags LIKE '%research%'"
)

for row in result.rows:
    print(f"{row['filename']}: {row['tags']}")
```

**Supported SQL Features:**
- Standard SELECT statements
- JOINs across all tables
- WHERE clauses with complex conditions
- GROUP BY and ORDER BY
- Aggregate functions (COUNT, SUM, AVG, etc.)
- Full-text search with FTS5 MATCH operator
- Subqueries and CTEs

#### `validate_query(sql: str) -> bool`

Validates a SQL query without executing it.

**Parameters:**
- `sql` (str): SQL query string

**Returns:**
- `bool`: True if query is valid, False otherwise

**Example:**
```python
if query_engine.validate_query("SELECT * FROM files"):
    print("Query is valid")
else:
    print("Query has syntax errors")
```

#### `get_schema() -> Dict[str, Any]`

Returns the database schema information.

**Returns:**
- `Dict[str, Any]`: Schema information including tables, columns, and indexes

**Example:**
```python
schema = query_engine.get_schema()
for table_name, table_info in schema['tables'].items():
    print(f"Table: {table_name}")
    for column in table_info['columns']:
        print(f"  - {column['name']} ({column['type']})")
```

### QueryResult Class

The `QueryResult` class contains the results of a query execution.

#### Properties

- `rows: List[Dict[str, Any]]` - List of result rows as dictionaries
- `columns: List[str]` - Column names in the result set
- `row_count: int` - Number of rows returned
- `execution_time: float` - Query execution time in seconds
- `sql: str` - The original SQL query

#### Methods

- `to_json() -> str` - Convert results to JSON string
- `to_csv() -> str` - Convert results to CSV string
- `to_table() -> str` - Convert results to formatted table string

**Example:**
```python
result = query_engine.execute_query("SELECT COUNT(*) as total FROM files")

print(f"Query: {result.sql}")
print(f"Execution time: {result.execution_time:.3f}s")
print(f"Results: {result.row_count} rows")
print(f"Total files: {result.rows[0]['total']}")

# Export in different formats
print("JSON:", result.to_json())
print("CSV:", result.to_csv())
print("Table:", result.to_table())
```

### Database Schema

The QueryEngine operates on the following main tables:

#### Files Table
```sql
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    directory TEXT NOT NULL,
    modified_date DATETIME NOT NULL,
    created_date DATETIME,
    file_size INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    heading_count INTEGER DEFAULT 0
);
```

#### Frontmatter Table
```sql
CREATE TABLE frontmatter (
    file_id INTEGER REFERENCES files(id),
    key TEXT NOT NULL,
    value TEXT,
    value_type TEXT NOT NULL,
    PRIMARY KEY (file_id, key)
);
```

#### Tags Table
```sql
CREATE TABLE tags (
    file_id INTEGER REFERENCES files(id),
    tag TEXT NOT NULL,
    source TEXT NOT NULL,
    PRIMARY KEY (file_id, tag)
);
```

#### Links Table
```sql
CREATE TABLE links (
    file_id INTEGER REFERENCES files(id),
    link_text TEXT,
    link_target TEXT NOT NULL,
    link_type TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE
);
```

#### Content FTS Table
```sql
CREATE VIRTUAL TABLE content_fts USING fts5(
    file_id UNINDEXED,
    title,
    content,
    headings
);
```

### Query Examples

#### Basic File Queries

```python
# Find all files
result = query_engine.execute_query("SELECT * FROM files")

# Find files by name pattern
result = query_engine.execute_query(
    "SELECT * FROM files WHERE filename LIKE '%.md'"
)

# Find recent files
result = query_engine.execute_query(
    "SELECT * FROM files WHERE modified_date > '2024-01-01' ORDER BY modified_date DESC"
)
```

#### Frontmatter Queries

```python
# Find files with specific frontmatter
result = query_engine.execute_query(
    "SELECT f.filename, fm.value as title FROM files f "
    "JOIN frontmatter fm ON f.id = fm.file_id "
    "WHERE fm.key = 'title' AND fm.value LIKE '%Research%'"
)

# Find files by author
result = query_engine.execute_query(
    "SELECT f.filename FROM files f "
    "JOIN frontmatter fm ON f.id = fm.file_id "
    "WHERE fm.key = 'author' AND fm.value = 'John Doe'"
)
```

#### Tag Queries

```python
# Find files with specific tags
result = query_engine.execute_query(
    "SELECT f.filename FROM files f "
    "JOIN tags t ON f.id = t.file_id "
    "WHERE t.tag = 'research'"
)

# Find most popular tags
result = query_engine.execute_query(
    "SELECT tag, COUNT(*) as count FROM tags "
    "GROUP BY tag ORDER BY count DESC LIMIT 10"
)

# Find files with multiple tags
result = query_engine.execute_query(
    "SELECT f.filename FROM files f "
    "WHERE f.id IN (SELECT file_id FROM tags WHERE tag = 'research') "
    "AND f.id IN (SELECT file_id FROM tags WHERE tag = 'project')"
)
```

#### Full-Text Search

```python
# Search content
result = query_engine.execute_query(
    "SELECT f.filename FROM files f "
    "JOIN content_fts fts ON f.id = fts.file_id "
    "WHERE content_fts MATCH 'markdown AND parsing'"
)

# Search titles and headings
result = query_engine.execute_query(
    "SELECT f.filename FROM files f "
    "JOIN content_fts fts ON f.id = fts.file_id "
    "WHERE fts.title MATCH 'project' OR fts.headings MATCH 'project'"
)
```

#### Link Analysis

```python
# Find files with external links
result = query_engine.execute_query(
    "SELECT f.filename, COUNT(l.link_target) as external_links FROM files f "
    "JOIN links l ON f.id = l.file_id "
    "WHERE l.is_internal = 0 "
    "GROUP BY f.id ORDER BY external_links DESC"
)

# Find broken internal links
result = query_engine.execute_query(
    "SELECT f.filename, l.link_target FROM files f "
    "JOIN links l ON f.id = l.file_id "
    "WHERE l.is_internal = 1 "
    "AND l.link_target NOT IN (SELECT filename FROM files)"
)
```

#### Advanced Analytics

```python
# Content statistics
result = query_engine.execute_query(
    "SELECT "
    "COUNT(*) as total_files, "
    "AVG(word_count) as avg_words, "
    "SUM(word_count) as total_words "
    "FROM files"
)

# Tag co-occurrence analysis
result = query_engine.execute_query(
    "SELECT t1.tag as tag1, t2.tag as tag2, COUNT(*) as co_occurrence "
    "FROM tags t1 "
    "JOIN tags t2 ON t1.file_id = t2.file_id AND t1.tag < t2.tag "
    "GROUP BY t1.tag, t2.tag "
    "ORDER BY co_occurrence DESC LIMIT 20"
)
```

### Security Features

- **SQL Injection Protection**: All queries are validated and parameterized
- **Query Complexity Limits**: Prevents resource-intensive queries
- **Timeout Protection**: Queries have configurable timeout limits
- **Read-Only Access**: QueryEngine only supports SELECT statements

### Performance Optimization

- **FTS5 Indexing**: Full-text search uses SQLite's FTS5 for fast text queries
- **Database Indexes**: Optimized indexes on frequently queried columns
- **Query Caching**: Results can be cached for repeated queries
- **Connection Pooling**: Efficient database connection management

### Error Handling

```python
from mdquery.exceptions import QueryError, ValidationError

try:
    result = query_engine.execute_query("INVALID SQL")
except ValidationError as e:
    print(f"Query validation failed: {e}")
except QueryError as e:
    print(f"Query execution failed: {e}")
```

### Integration Example

```python
from mdquery import Indexer, QueryEngine, CacheManager
from pathlib import Path

# Complete workflow
cache_manager = CacheManager("knowledge_base.db")
cache_manager.initialize_cache()

# Index notes
indexer = Indexer(cache_manager=cache_manager)
indexer.index_directory(Path("~/Documents/Notes"))

# Query notes
query_engine = QueryEngine(cache_manager=cache_manager)

# Find research notes from last month
result = query_engine.execute_query("""
    SELECT f.filename, f.modified_date, GROUP_CONCAT(t.tag) as tags
    FROM files f
    LEFT JOIN tags t ON f.id = t.file_id
    WHERE f.modified_date > date('now', '-1 month')
    AND (t.tag LIKE '%research%' OR f.filename LIKE '%research%')
    GROUP BY f.id
    ORDER BY f.modified_date DESC
""")

for row in result.rows:
    print(f"{row['filename']} ({row['modified_date']}) - Tags: {row['tags']}")
```

See also:
- [Indexer API](indexer.md)
- [CacheManager API](cache_manager.md)
- [Database Schema](../schema.md)