# Architecture Overview

This document provides a comprehensive overview of mdquery's system architecture, design decisions, and component interactions.

## System Overview

mdquery is designed as a modular system for indexing and querying markdown files using SQL-like syntax. The architecture emphasizes performance, extensibility, and ease of use.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   MCP Server    │    │  Python API     │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │      Core Engine            │
                    │  ┌─────────────────────────┐│
                    │  │    Query Engine         ││
                    │  └─────────────────────────┘│
                    │  ┌─────────────────────────┐│
                    │  │    Indexer              ││
                    │  └─────────────────────────┘│
                    │  ┌─────────────────────────┐│
                    │  │    Cache Manager        ││
                    │  └─────────────────────────┘│
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │    Data Layer               │
                    │  ┌─────────────────────────┐│
                    │  │    SQLite Database      ││
                    │  └─────────────────────────┘│
                    │  ┌─────────────────────────┐│
                    │  │    File System          ││
                    │  └─────────────────────────┘│
                    └─────────────────────────────┘
```

## Core Components

### 1. Query Engine (`query.py`)

The Query Engine is responsible for executing SQL queries against the indexed markdown data.

**Key Features:**
- SQL query parsing and validation
- Result formatting (JSON, CSV, table, markdown)
- Schema introspection
- Advanced query capabilities through `AdvancedQueryEngine`

**Design Patterns:**
- **Strategy Pattern**: Different result formatters
- **Template Method**: Query execution pipeline
- **Facade Pattern**: Simplified interface to complex database operations

```python
class QueryEngine:
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.db_manager = cache_manager.db_manager

    def execute_query(self, sql: str) -> QueryResult:
        # Validation -> Execution -> Formatting
        pass
```

### 2. Indexer (`indexer.py`)

The Indexer processes markdown files and extracts structured data for storage in the database.

**Key Features:**
- Incremental indexing (only process changed files)
- Multi-format support (Obsidian, Joplin, Jekyll, generic)
- Parallel processing for large directories
- Comprehensive metadata extraction

**Processing Pipeline:**
1. **File Discovery**: Scan directory for markdown files
2. **Change Detection**: Compare modification times
3. **Content Parsing**: Extract frontmatter, content, links, tags
4. **Data Storage**: Insert/update database records
5. **Statistics Collection**: Track processing metrics

```python
class Indexer:
    def index_directory(self, path: Path, recursive: bool = True) -> Dict:
        # Discovery -> Parsing -> Storage -> Statistics
        pass
```

### 3. Cache Manager (`cache.py`)

The Cache Manager handles database connections, schema management, and caching strategies.

**Key Features:**
- Database initialization and migration
- Connection pooling
- Query result caching
- Transaction management

**Caching Strategy:**
- **L1 Cache**: In-memory query result cache
- **L2 Cache**: Database-level optimizations
- **Cache Invalidation**: Based on file modification times

### 4. Database Manager (`database.py`)

Low-level database operations and schema management.

**Schema Design:**
```sql
-- Core tables
files: File metadata and content
frontmatter: Key-value pairs from YAML frontmatter
tags: Extracted tags with relationships
links: Markdown and wiki-style links
content_fts: Full-text search index

-- Indexes for performance
CREATE INDEX idx_files_path ON files(file_path);
CREATE INDEX idx_files_modified ON files(modified_date);
CREATE INDEX idx_tags_file ON tags(file_id);
CREATE INDEX idx_links_source ON links(source_file_id);
```

## Data Flow

### Indexing Flow

```
Markdown Files → File Scanner → Content Parser → Data Extractor → Database Storage
                      ↓              ↓              ↓              ↓
                 File Discovery  Frontmatter    Metadata      SQLite Tables
                 Change Detection   Content      Extraction    + FTS Index
                 Format Detection   Links/Tags   Validation    + Relationships
```

### Query Flow

```
SQL Query → Query Validator → Database Query → Result Formatter → Output
    ↓            ↓               ↓               ↓              ↓
User Input   Syntax Check   SQLite Execution  JSON/CSV/etc   CLI/API/MCP
Security     Schema Valid   Optimized Query   User Format    Response
```

## Design Principles

### 1. Modularity

Each component has a single responsibility and well-defined interfaces:
- **Separation of Concerns**: Parsing, storage, and querying are separate
- **Dependency Injection**: Components receive dependencies rather than creating them
- **Interface Segregation**: Small, focused interfaces

### 2. Performance

Optimized for handling large collections of markdown files:
- **Incremental Processing**: Only process changed files
- **Database Indexing**: Strategic indexes for common query patterns
- **Lazy Loading**: Load data only when needed
- **Connection Pooling**: Reuse database connections

### 3. Extensibility

Designed to support new formats and features:
- **Plugin Architecture**: New parsers can be added easily
- **Format Detection**: Automatic detection of markdown variants
- **Custom Queries**: Support for complex SQL operations
- **Multiple Interfaces**: CLI, Python API, MCP server

### 4. Reliability

Robust error handling and data integrity:
- **Transaction Safety**: Database operations are atomic
- **Error Recovery**: Graceful handling of malformed files
- **Data Validation**: Input validation at all levels
- **Comprehensive Testing**: Unit, integration, and performance tests

## Parser Architecture

### Parser Hierarchy

```python
class BaseParser:
    def parse(self, content: str, file_path: Path) -> ParsedContent

class FrontmatterParser(BaseParser):
    # YAML frontmatter extraction

class MarkdownParser(BaseParser):
    # Markdown content processing

class TagParser(BaseParser):
    # Tag extraction from content and frontmatter

class LinkParser(BaseParser):
    # Link extraction (markdown and wiki-style)
```

### Format-Specific Parsers

- **ObsidianParser**: Handles Obsidian-specific features (wikilinks, tags)
- **JoplinParser**: Processes Joplin export format
- **JekyllParser**: Handles Jekyll frontmatter and structure
- **GenericParser**: Fallback for standard markdown

## Advanced Features

### 1. Research Engine (`research.py`)

Provides advanced analysis capabilities:
- **Fuzzy Search**: Content similarity matching
- **Cross-Collection Search**: Query multiple note collections
- **Quote Attribution**: Extract and attribute quotes
- **Research Filtering**: Filter by date, topic, author, etc.

### 2. Advanced Query Engine (`advanced_queries.py`)

Extended query capabilities:
- **SEO Analysis**: Content optimization analysis
- **Structure Analysis**: Document hierarchy analysis
- **Similarity Detection**: Find related content
- **Link Analysis**: Relationship mapping
- **Content Reports**: Comprehensive analytics

### 3. MCP Server Integration

Model Context Protocol server for AI assistant integration:
- **Async Operations**: Non-blocking query execution
- **Tool Registration**: Expose functionality as MCP tools
- **Error Handling**: Graceful error responses
- **Thread Safety**: Concurrent request handling

## Performance Considerations

### Database Optimization

1. **Indexing Strategy**:
   - Primary keys on all tables
   - Foreign key indexes for joins
   - Composite indexes for common query patterns
   - Full-text search indexes for content

2. **Query Optimization**:
   - Use prepared statements
   - Limit result sets appropriately
   - Optimize JOIN operations
   - Use EXPLAIN QUERY PLAN for analysis

3. **Connection Management**:
   - Connection pooling for concurrent access
   - Transaction batching for bulk operations
   - Proper connection cleanup

### Memory Management

1. **Streaming Processing**:
   - Process large files in chunks
   - Use generators for large result sets
   - Lazy loading of file content

2. **Caching Strategy**:
   - LRU cache for frequently accessed data
   - Cache invalidation on file changes
   - Memory-bounded caches

### Scalability

1. **Horizontal Scaling**:
   - Multiple database files for different collections
   - Distributed indexing for large datasets
   - Load balancing for MCP server

2. **Vertical Scaling**:
   - Parallel processing during indexing
   - Optimized data structures
   - Efficient algorithms for similarity matching

## Security Considerations

### SQL Injection Prevention

- **Parameterized Queries**: All user input is parameterized
- **Query Validation**: SQL syntax validation before execution
- **Whitelist Approach**: Only allow safe SQL operations

### File System Security

- **Path Validation**: Prevent directory traversal attacks
- **Permission Checks**: Verify read permissions before processing
- **Sandboxing**: Limit file system access scope

### Data Privacy

- **Local Processing**: All data remains on user's machine
- **No Network Calls**: No external data transmission
- **Secure Storage**: Database files use appropriate permissions

## Error Handling Strategy

### Error Categories

1. **User Errors**: Invalid queries, missing files
2. **System Errors**: Database corruption, permission issues
3. **Data Errors**: Malformed markdown, encoding issues

### Error Recovery

1. **Graceful Degradation**: Continue processing when possible
2. **Detailed Logging**: Comprehensive error information
3. **User Feedback**: Clear error messages with suggestions
4. **Automatic Retry**: Retry transient failures

## Testing Architecture

### Test Categories

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Component interaction testing
3. **End-to-End Tests**: Complete workflow testing
4. **Performance Tests**: Speed and memory usage testing

### Test Infrastructure

- **Fixtures**: Reusable test data and setup
- **Mocking**: Isolate components during testing
- **Coverage**: Comprehensive code coverage tracking
- **CI/CD**: Automated testing on multiple platforms

## Future Architecture Considerations

### Planned Enhancements

1. **Plugin System**: Dynamic loading of custom parsers
2. **Distributed Storage**: Support for multiple database backends
3. **Real-time Indexing**: File system watching for automatic updates
4. **Advanced Analytics**: Machine learning-based content analysis

### Scalability Improvements

1. **Microservices**: Split into smaller, focused services
2. **Event-Driven Architecture**: Asynchronous processing pipeline
3. **Caching Layer**: Redis or similar for distributed caching
4. **API Gateway**: Centralized API management

This architecture provides a solid foundation for mdquery's current capabilities while allowing for future growth and enhancement.