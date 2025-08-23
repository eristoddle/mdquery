# Python API

The mdquery Python API provides direct access to all functionality for embedding in applications and custom scripts.

## Installation

```bash
pip install mdquery
```

## Quick Start

```python
from mdquery import Indexer, QueryEngine, CacheManager

# Initialize components
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# Index your notes
stats = indexer.index_directory("/path/to/notes")
print(f"Processed {stats['files_processed']} files")

# Query your data
result = query_engine.execute_query("SELECT * FROM files LIMIT 10")
if result.success:
    for row in result.data:
        print(f"File: {row['filename']}")
else:
    print(f"Query failed: {result.error}")
```

## Core Components

### CacheManager

Manages database connections, schema, and caching.

```python
from mdquery import CacheManager

# Initialize with default path
cache_manager = CacheManager()

# Initialize with custom path
cache_manager = CacheManager(
    db_path="custom/path/notes.db",
    cache_size=1000,
    enable_wal=True
)

# Initialize the database schema
cache_manager.initialize_cache()

# Get database statistics
stats = cache_manager.get_cache_stats()
print(f"Database size: {stats['db_size_mb']} MB")
```

#### Methods

##### `__init__(db_path=None, cache_size=500, enable_wal=True)`

Initialize cache manager.

**Parameters:**
- `db_path` (str, optional): Path to SQLite database file
- `cache_size` (int): Query result cache size (default: 500)
- `enable_wal` (bool): Enable WAL mode for better concurrency (default: True)

##### `initialize_cache()`

Initialize database schema and indexes.

```python
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()
```

##### `get_cache_stats()`

Get cache and database statistics.

**Returns:** Dictionary with cache statistics

```python
stats = cache_manager.get_cache_stats()
# {
#     'db_size_mb': 15.2,
#     'total_files': 1250,
#     'cache_hits': 45,
#     'cache_misses': 12
# }
```

##### `clear_cache()`

Clear query result cache.

```python
cache_manager.clear_cache()
```

### Indexer

Processes markdown files and extracts structured data.

```python
from mdquery import Indexer, CacheManager

cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)

# Index a directory
stats = indexer.index_directory("/path/to/notes")

# Index with options
stats = indexer.index_directory(
    path="/path/to/notes",
    recursive=True,
    file_extensions=['.md', '.markdown', '.txt']
)
```

#### Methods

##### `__init__(cache_manager, file_extensions=None)`

Initialize indexer.

**Parameters:**
- `cache_manager` (CacheManager): Cache manager instance
- `file_extensions` (list, optional): File extensions to process (default: ['.md', '.markdown'])

##### `index_directory(path, recursive=True, file_extensions=None)`

Index all markdown files in a directory.

**Parameters:**
- `path` (str|Path): Directory path to index
- `recursive` (bool): Scan subdirectories (default: True)
- `file_extensions` (list, optional): Override default file extensions

**Returns:** Dictionary with indexing statistics

```python
stats = indexer.index_directory("/path/to/notes")
# {
#     'files_processed': 45,
#     'files_updated': 3,
#     'files_skipped': 42,
#     'processing_time': 2.34,
#     'total_files': 45,
#     'errors': []
# }
```

##### `incremental_index_directory(path, recursive=True)`

Perform incremental indexing (only process changed files).

**Parameters:**
- `path` (str|Path): Directory path to index
- `recursive` (bool): Scan subdirectories (default: True)

**Returns:** Dictionary with indexing statistics

```python
stats = indexer.incremental_index_directory("/path/to/notes")
```

##### `index_file(file_path)`

Index a single file.

**Parameters:**
- `file_path` (str|Path): Path to file to index

**Returns:** Boolean indicating success

```python
success = indexer.index_file("/path/to/note.md")
```

##### `remove_file(file_path)`

Remove a file from the index.

**Parameters:**
- `file_path` (str|Path): Path to file to remove

```python
indexer.remove_file("/path/to/deleted-note.md")
```

### QueryEngine

Executes SQL queries against indexed data.

```python
from mdquery import QueryEngine, CacheManager

cache_manager = CacheManager("notes.db")
query_engine = QueryEngine(cache_manager=cache_manager)

# Execute query
result = query_engine.execute_query("SELECT * FROM files LIMIT 10")

# Format results
if result.success:
    json_output = query_engine.format_results(result, "json")
    csv_output = query_engine.format_results(result, "csv")
```

#### Methods

##### `__init__(cache_manager)`

Initialize query engine.

**Parameters:**
- `cache_manager` (CacheManager): Cache manager instance

##### `execute_query(sql, params=None)`

Execute SQL query.

**Parameters:**
- `sql` (str): SQL query to execute
- `params` (tuple, optional): Query parameters for prepared statements

**Returns:** QueryResult object

```python
# Simple query
result = query_engine.execute_query("SELECT COUNT(*) FROM files")

# Parameterized query
result = query_engine.execute_query(
    "SELECT * FROM files WHERE filename = ?",
    ("note.md",)
)

# Check result
if result.success:
    print(f"Found {len(result.data)} rows")
    for row in result.data:
        print(row)
else:
    print(f"Error: {result.error}")
```

##### `format_results(result, format_type)`

Format query results.

**Parameters:**
- `result` (QueryResult): Query result object
- `format_type` (str): Output format ("json", "csv", "table", "markdown")

**Returns:** Formatted string

```python
result = query_engine.execute_query("SELECT * FROM files LIMIT 5")

json_str = query_engine.format_results(result, "json")
csv_str = query_engine.format_results(result, "csv")
table_str = query_engine.format_results(result, "table")
markdown_str = query_engine.format_results(result, "markdown")
```

##### `get_schema()`

Get database schema information.

**Returns:** Dictionary with schema information

```python
schema = query_engine.get_schema()
# {
#     'tables': {
#         'files': {
#             'columns': [
#                 {'name': 'id', 'type': 'INTEGER', 'primary_key': True},
#                 {'name': 'filename', 'type': 'TEXT', 'nullable': False}
#             ]
#         }
#     },
#     'views': {},
#     'indexes': ['idx_files_path', 'idx_files_modified']
# }
```

##### `get_advanced_engine()`

Get advanced query engine for complex operations.

**Returns:** AdvancedQueryEngine instance

```python
advanced = query_engine.get_advanced_engine()
seo_analysis = advanced.analyze_seo()
```

### QueryResult

Result object returned by query execution.

#### Attributes

- `success` (bool): Whether query executed successfully
- `data` (list): Query result rows as dictionaries
- `error` (str): Error message if query failed
- `row_count` (int): Number of rows returned
- `execution_time` (float): Query execution time in seconds

#### Methods

##### `to_dict()`

Convert result to dictionary.

```python
result = query_engine.execute_query("SELECT * FROM files LIMIT 5")
result_dict = result.to_dict()
# {
#     'success': True,
#     'data': [...],
#     'row_count': 5,
#     'execution_time': 0.023,
#     'error': None
# }
```

## Advanced Features

### AdvancedQueryEngine

Provides advanced analysis capabilities.

```python
from mdquery import QueryEngine, CacheManager

cache_manager = CacheManager("notes.db")
query_engine = QueryEngine(cache_manager=cache_manager)
advanced_engine = query_engine.get_advanced_engine()

# SEO analysis
seo_results = advanced_engine.analyze_seo()
for analysis in seo_results:
    print(f"File: {analysis.file_path}, Score: {analysis.score}")

# Content structure analysis
structure_results = advanced_engine.analyze_content_structure()

# Find similar content
similar = advanced_engine.find_similar_content("research-paper.md", threshold=0.4)

# Link relationship analysis
links = advanced_engine.analyze_link_relationships()

# Generate comprehensive report
report = advanced_engine.generate_content_report()
```

### ResearchEngine

Research-focused analysis tools.

```python
from mdquery import QueryEngine, CacheManager
from mdquery.research import ResearchEngine, ResearchFilter
from datetime import datetime

cache_manager = CacheManager("notes.db")
query_engine = QueryEngine(cache_manager=cache_manager)
research_engine = ResearchEngine(query_engine)

# Fuzzy search
matches = research_engine.fuzzy_search(
    search_text="machine learning algorithms",
    threshold=0.7,
    max_results=20,
    search_fields=["content", "title", "headings"]
)

# Cross-collection search
results = research_engine.cross_collection_search(
    query_text="research methodology",
    collections=["papers", "notes", "drafts"],
    max_per_collection=10
)

# Extract quotes with attribution
quotes = research_engine.extract_quotes_with_attribution(
    file_paths=["research-paper.md"],
    quote_patterns=[r'"([^"]+)"', r'«([^»]+)»']
)

# Filter by research criteria
research_filter = ResearchFilter(
    date_from=datetime(2024, 1, 1),
    date_to=datetime(2024, 12, 31),
    topics=["ai", "machine-learning"],
    authors=["John Doe", "Jane Smith"]
)

filtered_results = research_engine.filter_by_research_criteria(research_filter)

# Generate research summary
summary = research_engine.generate_research_summary(research_filter)
```

## Error Handling

### Exception Types

```python
from mdquery.exceptions import (
    MDQueryError,
    DatabaseError,
    IndexingError,
    QueryError,
    ValidationError
)

try:
    result = query_engine.execute_query("INVALID SQL")
except QueryError as e:
    print(f"Query error: {e}")
except DatabaseError as e:
    print(f"Database error: {e}")
except MDQueryError as e:
    print(f"General error: {e}")
```

### Graceful Error Handling

```python
def safe_query(query_engine, sql):
    """Execute query with error handling."""
    try:
        result = query_engine.execute_query(sql)
        if result.success:
            return result.data
        else:
            print(f"Query failed: {result.error}")
            return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

# Usage
data = safe_query(query_engine, "SELECT * FROM files")
```

## Configuration

### Logging Configuration

```python
import logging
from mdquery.logging_config import setup_logging

# Setup logging
setup_logging(level=logging.INFO, log_file="mdquery.log")

# Custom logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)
```

### Database Configuration

```python
from mdquery import CacheManager

# Custom database configuration
cache_manager = CacheManager(
    db_path="custom/notes.db",
    cache_size=1000,           # Query result cache size
    enable_wal=True,           # Enable WAL mode
    timeout=30.0,              # Connection timeout
    check_same_thread=False    # Allow multi-threading
)
```

## Integration Examples

### Flask Web Application

```python
from flask import Flask, request, jsonify
from mdquery import QueryEngine, CacheManager

app = Flask(__name__)

# Initialize mdquery components
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()
query_engine = QueryEngine(cache_manager=cache_manager)

@app.route('/api/query', methods=['POST'])
def api_query():
    sql = request.json.get('sql')
    format_type = request.json.get('format', 'json')

    try:
        result = query_engine.execute_query(sql)
        if result.success:
            if format_type == 'json':
                return jsonify(result.to_dict())
            else:
                formatted = query_engine.format_results(result, format_type)
                return {'data': formatted}
        else:
            return jsonify({'error': result.error}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema')
def api_schema():
    schema = query_engine.get_schema()
    return jsonify(schema)

if __name__ == '__main__':
    app.run(debug=True)
```

### Jupyter Notebook Integration

```python
import pandas as pd
from mdquery import QueryEngine, CacheManager

# Initialize
cache_manager = CacheManager("notes.db")
query_engine = QueryEngine(cache_manager=cache_manager)

def query_to_dataframe(sql):
    """Execute query and return pandas DataFrame."""
    result = query_engine.execute_query(sql)
    if result.success:
        return pd.DataFrame(result.data)
    else:
        print(f"Query failed: {result.error}")
        return pd.DataFrame()

# Usage in notebook
df = query_to_dataframe("SELECT * FROM files")
df.head()

# Analyze data
tag_counts = query_to_dataframe("""
    SELECT tag, COUNT(*) as count
    FROM tags
    GROUP BY tag
    ORDER BY count DESC
    LIMIT 10
""")

# Visualize
import matplotlib.pyplot as plt
tag_counts.plot(x='tag', y='count', kind='bar')
plt.title('Most Common Tags')
plt.show()
```

### Automated Report Generation

```python
from mdquery import QueryEngine, CacheManager, Indexer
from datetime import datetime, timedelta
import json

class NotesReporter:
    def __init__(self, db_path):
        self.cache_manager = CacheManager(db_path)
        self.cache_manager.initialize_cache()
        self.query_engine = QueryEngine(cache_manager=self.cache_manager)
        self.indexer = Indexer(cache_manager=self.cache_manager)

    def update_index(self, notes_path):
        """Update index with latest changes."""
        stats = self.indexer.incremental_index_directory(notes_path)
        return stats

    def generate_daily_report(self):
        """Generate daily activity report."""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Files modified yesterday
        recent_files = self.query_engine.execute_query(f"""
            SELECT filename, title, word_count, modified_date
            FROM files
            WHERE DATE(modified_date) = '{yesterday}'
            ORDER BY modified_date DESC
        """)

        # Tag statistics
        tag_stats = self.query_engine.execute_query("""
            SELECT tag, COUNT(*) as count
            FROM tags
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 10
        """)

        # Word count statistics
        word_stats = self.query_engine.execute_query("""
            SELECT
                COUNT(*) as total_files,
                SUM(word_count) as total_words,
                AVG(word_count) as avg_words_per_file,
                MAX(word_count) as longest_file
            FROM files
        """)

        report = {
            'date': yesterday,
            'recent_files': recent_files.data if recent_files.success else [],
            'tag_statistics': tag_stats.data if tag_stats.success else [],
            'word_statistics': word_stats.data[0] if word_stats.success else {},
            'generated_at': datetime.now().isoformat()
        }

        return report

    def save_report(self, report, filename):
        """Save report to JSON file."""
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)

# Usage
reporter = NotesReporter("notes.db")
reporter.update_index("~/notes")
report = reporter.generate_daily_report()
reporter.save_report(report, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
```

### Custom Parser Integration

```python
from mdquery.parsers.base import BaseParser
from mdquery import Indexer, CacheManager
import re

class CustomTagParser(BaseParser):
    """Custom parser for special tag formats."""

    def parse(self, content, file_path):
        """Extract custom tags from content."""
        # Extract tags in format @tag or #tag
        tag_pattern = r'[@#](\w+)'
        tags = re.findall(tag_pattern, content)

        return {
            'tags': list(set(tags)),  # Remove duplicates
            'tag_count': len(set(tags))
        }

# Register custom parser
cache_manager = CacheManager("notes.db")
indexer = Indexer(cache_manager=cache_manager)

# Add custom parser to indexer
indexer.add_parser('custom_tags', CustomTagParser())

# Index with custom parser
stats = indexer.index_directory("~/notes")
```

## Performance Optimization

### Connection Pooling

```python
from mdquery import CacheManager
import threading

class ThreadSafeCacheManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._local = threading.local()

    def get_cache_manager(self):
        if not hasattr(self._local, 'cache_manager'):
            self._local.cache_manager = CacheManager(self.db_path)
            self._local.cache_manager.initialize_cache()
        return self._local.cache_manager

# Usage in multi-threaded application
thread_safe_cm = ThreadSafeCacheManager("notes.db")

def worker_function():
    cm = thread_safe_cm.get_cache_manager()
    query_engine = QueryEngine(cache_manager=cm)
    # Perform queries...
```

### Batch Processing

```python
def batch_index_files(indexer, file_paths, batch_size=100):
    """Index files in batches for better performance."""
    total_files = len(file_paths)
    processed = 0

    for i in range(0, total_files, batch_size):
        batch = file_paths[i:i + batch_size]

        for file_path in batch:
            try:
                indexer.index_file(file_path)
                processed += 1
            except Exception as e:
                print(f"Error indexing {file_path}: {e}")

        print(f"Processed {processed}/{total_files} files")

    return processed

# Usage
file_paths = [...]  # List of file paths
indexer = Indexer(cache_manager=cache_manager)
batch_index_files(indexer, file_paths)
```

### Query Optimization

```python
def optimized_content_search(query_engine, search_terms):
    """Optimized content search using FTS."""
    # Use full-text search for better performance
    sql = """
        SELECT f.filename, f.title,
               snippet(content_fts, 2, '<mark>', '</mark>', '...', 32) as snippet
        FROM files f
        JOIN content_fts fts ON f.id = fts.file_id
        WHERE content_fts MATCH ?
        ORDER BY rank
        LIMIT 50
    """

    result = query_engine.execute_query(sql, (search_terms,))
    return result.data if result.success else []

# Usage
results = optimized_content_search(query_engine, "machine learning")
```

This Python API provides complete programmatic access to mdquery functionality, enabling powerful integrations and custom applications.