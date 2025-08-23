# Interface APIs

This section documents the various interfaces available for interacting with mdquery.

## Available Interfaces

- **[CLI Interface](cli.md)** - Command-line interface documentation
- **[MCP Server](mcp-server.md)** - Model Context Protocol server for AI integration
- **[Python API](python-api.md)** - Direct Python library usage

## Interface Comparison

| Feature | CLI | MCP Server | Python API |
|---------|-----|------------|------------|
| **Use Case** | Interactive use, scripting | AI assistant integration | Application embedding |
| **Query Execution** | ✅ | ✅ | ✅ |
| **Indexing** | ✅ | ✅ | ✅ |
| **Advanced Analytics** | ✅ | ✅ | ✅ |
| **Real-time Processing** | ❌ | ✅ | ✅ |
| **Async Support** | ❌ | ✅ | ✅ |
| **Custom Integration** | ❌ | ❌ | ✅ |

## Quick Start Examples

### CLI Interface
```bash
# Index your notes
mdquery index ~/notes

# Query your data
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"

# Get schema information
mdquery schema
```

### MCP Server
```json
{
  "method": "tools/call",
  "params": {
    "name": "query_markdown",
    "arguments": {
      "sql": "SELECT filename, title FROM files LIMIT 10",
      "format": "json"
    }
  }
}
```

### Python API
```python
from mdquery import Indexer, QueryEngine, CacheManager

# Initialize components
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# Index and query
indexer.index_directory("~/notes")
result = query_engine.execute_query("SELECT * FROM files")
```

## Authentication and Security

### CLI Interface
- No authentication required (local use)
- File system permissions apply
- SQL injection protection through parameterized queries

### MCP Server
- No built-in authentication (runs locally)
- Designed for trusted AI assistant integration
- Same SQL injection protections as CLI

### Python API
- Direct library access (no network layer)
- Application-level security responsibility
- Full access to all functionality

## Error Handling

All interfaces provide consistent error handling:

- **Validation Errors**: Invalid SQL syntax, missing files
- **System Errors**: Database issues, permission problems
- **Data Errors**: Malformed markdown, encoding issues

Error responses include:
- Error type and code
- Descriptive error message
- Suggested resolution steps
- Context information where applicable

## Performance Considerations

### CLI Interface
- Optimized for single-operation use
- Database connection per command
- Suitable for scripting and automation

### MCP Server
- Persistent connections for better performance
- Async processing for concurrent requests
- Connection pooling for scalability

### Python API
- Most efficient for multiple operations
- Direct access without serialization overhead
- Full control over resource management

## Integration Patterns

### Batch Processing (CLI)
```bash
#!/bin/bash
# Process multiple directories
for dir in ~/notes/*/; do
    mdquery index "$dir"
done

# Generate reports
mdquery query "SELECT tag, COUNT(*) FROM tags GROUP BY tag" --format csv > tag_report.csv
```

### AI Assistant Integration (MCP)
```python
# AI assistant can call these tools:
# - query_markdown: Execute SQL queries
# - index_directory: Index new content
# - get_schema: Understand data structure
# - analyze_seo: Content optimization
# - fuzzy_search: Find similar content
```

### Application Embedding (Python API)
```python
class NotesManager:
    def __init__(self, db_path: str):
        self.cache_manager = CacheManager(db_path)
        self.indexer = Indexer(cache_manager=self.cache_manager)
        self.query_engine = QueryEngine(cache_manager=self.cache_manager)

    def search_notes(self, query: str) -> List[Dict]:
        sql = """
        SELECT f.filename, f.title
        FROM files f
        JOIN content_fts fts ON f.id = fts.file_id
        WHERE content_fts MATCH ?
        """
        result = self.query_engine.execute_query(sql, (query,))
        return result.data if result.success else []
```

## Configuration

### CLI Configuration
Configuration via command-line arguments and environment variables:
```bash
export MDQUERY_DB_PATH=~/notes/mdquery.db
export MDQUERY_CACHE_DIR=~/notes/.cache
```

### MCP Server Configuration
Configuration via initialization parameters:
```python
server = MDQueryMCPServer(
    db_path=Path("~/notes/mdquery.db"),
    cache_dir=Path("~/notes/.cache")
)
```

### Python API Configuration
Direct configuration through constructor parameters:
```python
cache_manager = CacheManager(
    db_path="notes.db",
    cache_size=1000,
    enable_wal=True
)
```

## Best Practices

### CLI Interface
- Use absolute paths for reliability
- Pipe output to files for large results
- Use `--format` option for structured data
- Check exit codes in scripts

### MCP Server
- Handle async operations properly
- Implement proper error handling
- Use appropriate timeouts
- Monitor resource usage

### Python API
- Initialize components once and reuse
- Use context managers for resource cleanup
- Handle exceptions appropriately
- Close database connections properly

## Migration Between Interfaces

### CLI to Python API
```python
# CLI: mdquery query "SELECT * FROM files"
# Python API:
result = query_engine.execute_query("SELECT * FROM files")
data = result.data
```

### CLI to MCP Server
```python
# CLI: mdquery index ~/notes
# MCP Server tool call:
await index_directory(path="~/notes", recursive=True, incremental=True)
```

### Python API to MCP Server
```python
# Python API: Direct method calls
# MCP Server: Async tool calls with JSON serialization
result = await query_markdown(sql="SELECT * FROM files", format="json")
data = json.loads(result)
```