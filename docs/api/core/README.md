# Core Components

This section documents the core components that make up mdquery's architecture.

## Components Overview

- **[Indexer](indexer.md)** - Processes markdown files and extracts structured data
- **[QueryEngine](query-engine.md)** - Executes SQL queries against indexed data
- **[CacheManager](cache-manager.md)** - Manages database connections and caching
- **[DatabaseManager](database-manager.md)** - Low-level database operations
- **[Parsers](parsers.md)** - Content parsing and extraction components

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Indexer      │    │  QueryEngine    │    │  CacheManager   │
│                 │    │                 │    │                 │
│ - File scanning │    │ - SQL execution │    │ - DB connections│
│ - Content parse │    │ - Result format │    │ - Query caching │
│ - Data extract  │    │ - Schema info   │    │ - Transaction   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │    DatabaseManager          │
                    │                             │
                    │ - SQLite operations         │
                    │ - Schema management         │
                    │ - Index optimization        │
                    └─────────────────────────────┘
```

## Component Interactions

### Indexing Flow

1. **Indexer** scans directories for markdown files
2. **Parsers** extract content, frontmatter, tags, and links
3. **DatabaseManager** stores structured data in SQLite
4. **CacheManager** manages transactions and connections

### Query Flow

1. **QueryEngine** receives SQL query
2. **CacheManager** checks query cache
3. **DatabaseManager** executes query against SQLite
4. **QueryEngine** formats and returns results

## Key Design Patterns

### Dependency Injection

Components receive their dependencies rather than creating them:

```python
# Good: Dependencies injected
cache_manager = CacheManager("notes.db")
indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# Bad: Components create their own dependencies
indexer = Indexer("notes.db")  # Creates its own database connection
```

### Single Responsibility

Each component has a focused responsibility:

- **Indexer**: Only handles file processing and data extraction
- **QueryEngine**: Only handles query execution and formatting
- **CacheManager**: Only handles caching and database connections
- **DatabaseManager**: Only handles low-level database operations

### Interface Segregation

Components expose minimal, focused interfaces:

```python
class Indexer:
    def index_directory(self, path: Path) -> Dict: ...
    def index_file(self, file_path: Path) -> bool: ...
    def remove_file(self, file_path: Path) -> None: ...

class QueryEngine:
    def execute_query(self, sql: str) -> QueryResult: ...
    def format_results(self, result: QueryResult, format: str) -> str: ...
    def get_schema(self) -> Dict: ...
```

## Error Handling Strategy

### Exception Hierarchy

```python
MDQueryError                    # Base exception
├── DatabaseError              # Database-related errors
├── IndexingError              # File processing errors
├── QueryError                 # SQL execution errors
├── ValidationError            # Input validation errors
└── ConfigurationError         # Configuration errors
```

### Error Recovery

Components implement graceful error handling:

1. **Validation**: Input validation before processing
2. **Isolation**: Errors in one file don't stop batch processing
3. **Logging**: Comprehensive error logging for debugging
4. **Recovery**: Automatic retry for transient failures

## Performance Considerations

### Database Optimization

- **Connection Pooling**: Reuse database connections
- **Transaction Batching**: Group operations for efficiency
- **Index Strategy**: Strategic indexes for common queries
- **WAL Mode**: Write-Ahead Logging for better concurrency

### Memory Management

- **Streaming**: Process large files in chunks
- **Lazy Loading**: Load data only when needed
- **Cache Limits**: Bounded caches to prevent memory leaks
- **Resource Cleanup**: Proper cleanup of resources

### Concurrency

- **Thread Safety**: Components are thread-safe where needed
- **Async Support**: Async operations for I/O-bound tasks
- **Lock-Free**: Minimize locking for better performance

## Configuration

### Component Configuration

Each component accepts configuration through constructor parameters:

```python
# CacheManager configuration
cache_manager = CacheManager(
    db_path="notes.db",
    cache_size=1000,
    enable_wal=True,
    timeout=30.0
)

# Indexer configuration
indexer = Indexer(
    cache_manager=cache_manager,
    file_extensions=['.md', '.markdown', '.txt'],
    max_file_size=10 * 1024 * 1024  # 10MB
)

# QueryEngine configuration
query_engine = QueryEngine(
    cache_manager=cache_manager,
    default_limit=100,
    enable_explain=True
)
```

### Environment Variables

Components respect environment variables for configuration:

- `MDQUERY_DB_PATH`: Default database path
- `MDQUERY_CACHE_SIZE`: Query cache size
- `MDQUERY_LOG_LEVEL`: Logging level
- `MDQUERY_MAX_FILE_SIZE`: Maximum file size to process

## Testing Strategy

### Unit Testing

Each component is tested in isolation:

```python
def test_indexer_processes_markdown_file():
    # Arrange
    mock_cache_manager = Mock()
    indexer = Indexer(cache_manager=mock_cache_manager)

    # Act
    result = indexer.index_file("test.md")

    # Assert
    assert result is True
    mock_cache_manager.store_file_data.assert_called_once()
```

### Integration Testing

Components are tested together:

```python
def test_indexer_query_engine_integration():
    # Arrange
    cache_manager = CacheManager(":memory:")
    cache_manager.initialize_cache()

    indexer = Indexer(cache_manager=cache_manager)
    query_engine = QueryEngine(cache_manager=cache_manager)

    # Act
    indexer.index_file("test.md")
    result = query_engine.execute_query("SELECT COUNT(*) FROM files")

    # Assert
    assert result.success
    assert result.data[0]['COUNT(*)'] == 1
```

### Mock Objects

Components use dependency injection to enable easy mocking:

```python
class MockCacheManager:
    def __init__(self):
        self.stored_data = []

    def store_file_data(self, file_data):
        self.stored_data.append(file_data)

    def get_file_data(self, file_path):
        return next((d for d in self.stored_data if d['path'] == file_path), None)
```

## Extension Points

### Custom Parsers

Add custom parsers for specialized content:

```python
from mdquery.parsers.base import BaseParser

class CustomParser(BaseParser):
    def parse(self, content: str, file_path: Path) -> Dict:
        # Custom parsing logic
        return {'custom_data': extracted_data}

# Register with indexer
indexer.add_parser('custom', CustomParser())
```

### Custom Formatters

Add custom result formatters:

```python
from mdquery.formatters.base import BaseFormatter

class CustomFormatter(BaseFormatter):
    def format(self, result: QueryResult) -> str:
        # Custom formatting logic
        return formatted_output

# Register with query engine
query_engine.add_formatter('custom', CustomFormatter())
```

### Database Extensions

Extend database schema for custom data:

```python
def extend_schema(db_manager):
    db_manager.execute("""
        CREATE TABLE IF NOT EXISTS custom_data (
            id INTEGER PRIMARY KEY,
            file_id INTEGER REFERENCES files(id),
            custom_field TEXT
        )
    """)

    db_manager.execute("""
        CREATE INDEX idx_custom_data_file_id ON custom_data(file_id)
    """)
```

## Best Practices

### Component Initialization

Always initialize components in the correct order:

```python
# 1. Initialize cache manager first
cache_manager = CacheManager("notes.db")
cache_manager.initialize_cache()

# 2. Initialize other components with cache manager
indexer = Indexer(cache_manager=cache_manager)
query_engine = QueryEngine(cache_manager=cache_manager)

# 3. Use components
indexer.index_directory("~/notes")
result = query_engine.execute_query("SELECT * FROM files")
```

### Resource Management

Use context managers for proper resource cleanup:

```python
class ManagedCacheManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.cache_manager = None

    def __enter__(self):
        self.cache_manager = CacheManager(self.db_path)
        self.cache_manager.initialize_cache()
        return self.cache_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cache_manager:
            self.cache_manager.close()

# Usage
with ManagedCacheManager("notes.db") as cache_manager:
    indexer = Indexer(cache_manager=cache_manager)
    indexer.index_directory("~/notes")
```

### Error Handling

Implement comprehensive error handling:

```python
def safe_index_directory(indexer, path):
    try:
        stats = indexer.index_directory(path)
        return stats
    except IndexingError as e:
        logger.error(f"Indexing failed: {e}")
        return {'error': str(e)}
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {'error': 'Unexpected error occurred'}
```

### Configuration Management

Use configuration objects for complex setups:

```python
@dataclass
class MDQueryConfig:
    db_path: str = "notes.db"
    cache_size: int = 1000
    enable_wal: bool = True
    file_extensions: List[str] = field(default_factory=lambda: ['.md', '.markdown'])
    max_file_size: int = 10 * 1024 * 1024

def create_components(config: MDQueryConfig):
    cache_manager = CacheManager(
        db_path=config.db_path,
        cache_size=config.cache_size,
        enable_wal=config.enable_wal
    )

    indexer = Indexer(
        cache_manager=cache_manager,
        file_extensions=config.file_extensions,
        max_file_size=config.max_file_size
    )

    query_engine = QueryEngine(cache_manager=cache_manager)

    return cache_manager, indexer, query_engine
```

This core components documentation provides a comprehensive understanding of mdquery's internal architecture and how the components work together to provide powerful markdown querying capabilities.