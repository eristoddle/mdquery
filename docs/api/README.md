# mdquery API Documentation

This directory contains comprehensive API documentation for mdquery components.

## Structure

- `core/` - Core engine components (Indexer, QueryEngine, CacheManager)
- `parsers/` - Parser components (Frontmatter, Markdown, Tags, Links)
- `interfaces/` - Client interfaces (CLI, MCP Server)
- `examples/` - Code examples and usage patterns

## Quick Start

```python
from mdquery import Indexer, QueryEngine, CacheManager

# Initialize components
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# Index your notes
indexer.index_directory("/path/to/notes")

# Query your notes
result = query_engine.execute_query(
    "SELECT * FROM files WHERE tags LIKE '%research%'"
)

for row in result.rows:
    print(f"{row['filename']}: {row['tags']}")
```

## Key Concepts

- **Indexer**: Scans directories and parses markdown files into the database
- **QueryEngine**: Executes SQL queries against the indexed data
- **CacheManager**: Manages SQLite database lifecycle and caching
- **Parsers**: Extract specific data types (frontmatter, tags, links) from markdown

## Database Schema

See [Database Schema](schema.md) for complete table definitions and relationships.