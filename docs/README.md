# mdquery Documentation

Complete documentation for mdquery - the universal markdown querying tool.

## Documentation Structure

### User Guide
- **[Getting Started](user-guide/README.md)** - Introduction and quick start
- **[Query Syntax](user-guide/query-syntax.md)** - Complete SQL syntax guide
- **[MCP Integration](user-guide/mcp-integration.md)** - AI assistant integration guide
- **[Best Practices](user-guide/best-practices.md)** - Tips for effective usage
- **[Examples](user-guide/examples/)** - Real-world usage examples

### API Reference
- **[Core Components](api/core/)** - Indexer, QueryEngine, CacheManager
- **[Parsers](api/parsers/)** - Frontmatter, Markdown, Tags, Links
- **[Interfaces](api/interfaces/)** - CLI and MCP Server APIs
- **[Database Schema](api/schema.md)** - Complete schema reference

### Development
- **[Contributing](development/contributing.md)** - How to contribute
- **[Testing](development/testing.md)** - Running and writing tests
- **[Architecture](development/architecture.md)** - System design overview

## Quick Reference

### Installation
```bash
pip install mdquery
```

### Basic Usage
```bash
# Index your notes
mdquery index /path/to/notes

# Query your notes
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"

# View schema
mdquery schema
```

### Python API
```python
from mdquery import Indexer, QueryEngine, CacheManager

# Initialize
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# Index and query
indexer.index_directory("/path/to/notes")
result = query_engine.execute_query("SELECT * FROM files")
```

## Key Features

- **Universal Compatibility**: Works with Obsidian, Joplin, Jekyll, and generic markdown
- **SQL-Like Queries**: Familiar syntax for powerful searches
- **Full-Text Search**: Fast content search with SQLite FTS5
- **Rich Metadata**: Query frontmatter, tags, links, and content
- **High Performance**: Efficient indexing and caching
- **Multiple Interfaces**: CLI tool and MCP server for AI integration

## Database Schema Overview

mdquery organizes your markdown files into these main tables:

- **`files`** - File metadata (path, dates, word count, etc.)
- **`frontmatter`** - YAML frontmatter key-value pairs
- **`tags`** - Tags from frontmatter and content
- **`links`** - Markdown and wikilinks
- **`content_fts`** - Full-text searchable content

## Common Query Patterns

### Find Recent Files
```sql
SELECT filename, modified_date FROM files
WHERE modified_date > '2024-01-01'
ORDER BY modified_date DESC;
```

### Search Content
```sql
SELECT f.filename FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'machine learning';
```

### Analyze Tags
```sql
SELECT tag, COUNT(*) as usage FROM tags
GROUP BY tag ORDER BY usage DESC LIMIT 10;
```

### Find Related Notes
```sql
SELECT f.filename, GROUP_CONCAT(t.tag) as tags
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('research', 'ai', 'ml')
GROUP BY f.id;
```

## Support and Community

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Ask questions and share tips
- **Documentation**: Complete guides and examples
- **Examples**: Real-world usage patterns

## What's New

See the [Changelog](CHANGELOG.md) for recent updates and new features.

---

Ready to get started? Head to the [User Guide](user-guide/README.md) for installation and setup instructions.