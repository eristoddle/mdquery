# MCP Server API

The mdquery MCP (Model Context Protocol) server provides AI assistants with powerful markdown querying capabilities. This document covers installation, configuration, and usage of the MCP server.

## Overview

The MCP server exposes mdquery functionality through standardized tools that AI assistants can call to:
- Query markdown databases with SQL
- Index new content automatically
- Perform advanced content analysis
- Generate research summaries and reports

## Installation

### Prerequisites

- Python 3.8 or higher
- mdquery package installed
- MCP-compatible AI assistant (Claude Desktop, etc.)

### Install mdquery with MCP support

```bash
pip install mdquery[mcp]
```

### Configure AI Assistant

Add mdquery MCP server to your AI assistant configuration:

#### Claude Desktop Configuration

Add to `~/.claude/claude_desktop_config.json`:

#### Basic Configuration (Single Notes Directory)
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/notes",
        "MDQUERY_DB_PATH": "/path/to/your/notes.db",
        "MDQUERY_CACHE_DIR": "/path/to/cache"
      }
    }
  }
}
```

#### Multiple Directories (Comma-separated)
```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/notes,/path/to/docs,/path/to/research",
        "MDQUERY_DB_PATH": "/path/to/your/notes.db",
        "MDQUERY_CACHE_DIR": "/path/to/cache"
      }
    }
  }
}
```

#### Multiple Directories (Separate Servers)
```json
{
  "mcpServers": {
    "mdquery-personal": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/personal/notes",
        "MDQUERY_DB_PATH": "/path/to/personal.db"
      }
    },
    "mdquery-work": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/work/docs",
        "MDQUERY_DB_PATH": "/path/to/work.db"
      }
    }
  }
}
```

#### Alternative: Direct Server Start

```bash
# Start MCP server directly
python -m mdquery.mcp_server

# With auto-indexing of notes directory
MDQUERY_NOTES_DIR=~/Documents/Notes python -m mdquery.mcp_server

# Or with custom database path only
MDQUERY_DB_PATH=~/notes/mdquery.db python -m mdquery.mcp_server
```

## Available Tools

### Core Query Tools

#### `query_markdown`

Execute SQL queries against your markdown database.

**Parameters:**
- `sql` (string, required): SQL query to execute
- `format` (string, optional): Output format - "json", "csv", "table", "markdown" (default: "json")

**Example:**
```json
{
  "name": "query_markdown",
  "arguments": {
    "sql": "SELECT filename, title FROM files WHERE tags LIKE '%research%' LIMIT 10",
    "format": "json"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "filename": "research-notes.md",
      "title": "Research Notes on AI"
    }
  ],
  "row_count": 1,
  "execution_time": 0.023
}
```

#### `get_schema`

Get database schema information to understand available tables and columns.

**Parameters:**
- `table` (string, optional): Specific table to get schema for

**Example:**
```json
{
  "name": "get_schema",
  "arguments": {
    "table": "files"
  }
}
```

**Response:**
```json
{
  "table": "files",
  "schema": {
    "columns": [
      {"name": "id", "type": "INTEGER", "primary_key": true},
      {"name": "filename", "type": "TEXT", "nullable": false},
      {"name": "file_path", "type": "TEXT", "nullable": false},
      {"name": "title", "type": "TEXT"},
      {"name": "created_date", "type": "DATETIME"},
      {"name": "modified_date", "type": "DATETIME"},
      {"name": "word_count", "type": "INTEGER"}
    ]
  }
}
```

### Indexing Tools

#### `index_directory`

Index markdown files in a single directory.

**Parameters:**
- `path` (string, required): Directory path to index
- `recursive` (boolean, optional): Scan subdirectories (default: true)
- `incremental` (boolean, optional): Use incremental indexing (default: true)

**Example:**
```json
{
  "name": "index_directory",
  "arguments": {
    "path": "~/Documents/Notes",
    "recursive": true,
    "incremental": true
  }
}
```

**Response:**
```json
{
  "path": "/Users/username/Documents/Notes",
  "recursive": true,
  "incremental": true,
  "statistics": {
    "files_processed": 45,
    "files_updated": 3,
    "files_skipped": 42,
    "processing_time": 2.34,
    "total_files": 45
  }
}
```

#### `index_multiple_directories`

Index markdown files in multiple directories at once.

**Parameters:**
- `paths` (string, required): Comma-separated list of directory paths to index
- `recursive` (boolean, optional): Scan subdirectories (default: true)
- `incremental` (boolean, optional): Use incremental indexing (default: true)

**Example:**
```json
{
  "name": "index_multiple_directories",
  "arguments": {
    "paths": "~/Documents/Notes,~/Projects/Documentation,~/Research/Papers",
    "recursive": true,
    "incremental": true
  }
}
```

**Response:**
```json
{
  "paths": [
    "/Users/username/Documents/Notes",
    "/Users/username/Projects/Documentation",
    "/Users/username/Research/Papers"
  ],
  "recursive": true,
  "incremental": true,
  "statistics": {
    "/Users/username/Documents/Notes": {
      "files_processed": 45,
      "files_updated": 3,
      "files_skipped": 42,
      "processing_time": 2.34,
      "total_files": 45
    },
    "/Users/username/Projects/Documentation": {
      "files_processed": 23,
      "files_updated": 1,
      "files_skipped": 22,
      "processing_time": 1.12,
      "total_files": 23
    },
    "/Users/username/Research/Papers": {
      "files_processed": 67,
      "files_updated": 5,
      "files_skipped": 62,
      "processing_time": 3.45,
      "total_files": 67
    }
  }
}
```

### Content Analysis Tools

#### `analyze_seo`

Perform SEO analysis on markdown files.

**Parameters:**
- `files` (string, optional): Comma-separated list of specific files to analyze

**Example:**
```json
{
  "name": "analyze_seo",
  "arguments": {
    "files": "blog-post.md,article.md"
  }
}
```

**Response:**
```json
[
  {
    "file_path": "blog-post.md",
    "title": "How to Use mdquery",
    "description": "A comprehensive guide to querying markdown files",
    "word_count": 1250,
    "heading_count": 8,
    "tags": ["tutorial", "mdquery", "markdown"],
    "issues": ["Missing meta description", "H1 tag not found"],
    "score": 75
  }
]
```

#### `analyze_content_structure`

Analyze document structure and hierarchy.

**Parameters:**
- `files` (string, optional): Comma-separated list of specific files to analyze

**Example:**
```json
{
  "name": "analyze_content_structure",
  "arguments": {}
}
```

**Response:**
```json
[
  {
    "file_path": "document.md",
    "heading_hierarchy": [
      {"level": 1, "text": "Main Title"},
      {"level": 2, "text": "Section 1"},
      {"level": 3, "text": "Subsection 1.1"}
    ],
    "word_count": 850,
    "paragraph_count": 12,
    "readability_score": 68.5,
    "structure_issues": ["Missing H2 after H1", "Deep nesting detected"]
  }
]
```

#### `find_similar_content`

Find content similar to a specified file.

**Parameters:**
- `file_path` (string, required): Path of the file to find similar content for
- `threshold` (number, optional): Minimum similarity score 0.0-1.0 (default: 0.3)

**Example:**
```json
{
  "name": "find_similar_content",
  "arguments": {
    "file_path": "research-paper.md",
    "threshold": 0.4
  }
}
```

**Response:**
```json
[
  {
    "file1_path": "research-paper.md",
    "file2_path": "related-study.md",
    "common_tags": ["research", "ai", "machine-learning"],
    "similarity_score": 0.67,
    "total_tags_file1": 8,
    "total_tags_file2": 6
  }
]
```

### Research Tools

#### `fuzzy_search`

Perform fuzzy text matching for content discovery.

**Parameters:**
- `search_text` (string, required): Text to search for
- `threshold` (number, optional): Minimum similarity score (default: 0.6)
- `max_results` (number, optional): Maximum results to return (default: 50)
- `search_fields` (string, optional): Fields to search in (default: "content,title,headings")

**Example:**
```json
{
  "name": "fuzzy_search",
  "arguments": {
    "search_text": "machine learning algorithms",
    "threshold": 0.7,
    "max_results": 20
  }
}
```

**Response:**
```json
[
  {
    "file_path": "ml-notes.md",
    "matched_text": "machine learning algorithm implementation",
    "similarity_score": 0.85,
    "context_before": "This section covers",
    "context_after": "with practical examples",
    "match_type": "content",
    "line_number": 42
  }
]
```

#### `generate_research_summary`

Generate comprehensive research summary and statistics.

**Parameters:**
- `date_from` (string, optional): Filter from date (YYYY-MM-DD)
- `date_to` (string, optional): Filter to date (YYYY-MM-DD)
- `topics` (string, optional): Filter by topics/tags (comma-separated)
- `sources` (string, optional): Filter by source paths (comma-separated)
- `authors` (string, optional): Filter by authors (comma-separated)
- `collections` (string, optional): Filter by collections/directories (comma-separated)

**Example:**
```json
{
  "name": "generate_research_summary",
  "arguments": {
    "date_from": "2024-01-01",
    "topics": "ai,machine-learning,research"
  }
}
```

**Response:**
```json
{
  "summary": {
    "total_files": 156,
    "total_words": 45230,
    "date_range": {
      "earliest": "2024-01-15",
      "latest": "2024-03-20"
    },
    "top_topics": [
      {"topic": "machine-learning", "count": 45},
      {"topic": "ai", "count": 38},
      {"topic": "research", "count": 32}
    ],
    "authors": [
      {"author": "John Doe", "files": 23},
      {"author": "Jane Smith", "files": 18}
    ],
    "collections": [
      {"collection": "research-papers", "files": 67},
      {"collection": "notes", "files": 89}
    ]
  }
}
```

### Utility Tools

#### `get_file_content`

Retrieve content and metadata of a specific file.

**Parameters:**
- `file_path` (string, required): Path to the file
- `include_parsed` (boolean, optional): Include parsed content (default: false)

**Example:**
```json
{
  "name": "get_file_content",
  "arguments": {
    "file_path": "important-note.md",
    "include_parsed": true
  }
}
```

**Response:**
```json
{
  "path": "/path/to/important-note.md",
  "filename": "important-note.md",
  "content": "# Important Note\n\nThis is the content...",
  "metadata": {
    "size": 1024,
    "modified": "2024-03-15T10:30:00Z",
    "word_count": 150
  },
  "parsed": {
    "frontmatter": {
      "title": "Important Note",
      "tags": ["important", "note"]
    },
    "tags": ["important", "note", "content-tag"],
    "links": [
      {"type": "markdown", "target": "related-note.md", "text": "Related Note"}
    ]
  }
}
```

## Configuration

### Environment Variables

- `MDQUERY_NOTES_DIR`: Directory containing markdown files to auto-index on startup (optional)
- `MDQUERY_DB_PATH`: Path to SQLite database file (default: `~/.mdquery/mdquery.db`)
- `MDQUERY_CACHE_DIR`: Directory for cache files (default: `~/.mdquery/cache`)
- `MDQUERY_LOG_LEVEL`: Logging level (default: `INFO`)

### Configuration Strategies

#### Single Notes Directory (Recommended)
Set `MDQUERY_NOTES_DIR` to automatically index your main notes directory on startup:

```bash
export MDQUERY_NOTES_DIR=~/Documents/Notes
export MDQUERY_DB_PATH=~/.mdquery/notes.db
```

#### Multiple Notes Directories (Comma-separated)
Set `MDQUERY_NOTES_DIR` to comma-separated directories:

```bash
export MDQUERY_NOTES_DIR=~/Documents/Notes,~/Work/Docs,~/Research/Papers
export MDQUERY_DB_PATH=~/.mdquery/all-notes.db
```

#### Multiple Notes Directories (Separate Servers)
Use separate server configurations for independent databases:

```bash
# Server 1
export MDQUERY_NOTES_DIR=~/Documents/Notes
export MDQUERY_DB_PATH=~/.mdquery/personal.db

# Server 2
export MDQUERY_NOTES_DIR=~/Work/Docs
export MDQUERY_DB_PATH=~/.mdquery/work.db
```

#### Manual Indexing Only
Don't set `MDQUERY_NOTES_DIR` and use indexing tools as needed:

```bash
export MDQUERY_DB_PATH=~/.mdquery/manual.db
```

### Server Initialization

```python
from mdquery.mcp import MDQueryMCPServer
from pathlib import Path

# Initialize with single notes directory
server = MDQueryMCPServer(
    db_path=Path("~/notes/mdquery.db"),
    cache_dir=Path("~/notes/.cache"),
    notes_dirs=[Path("~/Documents/Notes")]  # Auto-index on startup
)

# Initialize with multiple notes directories
server = MDQueryMCPServer(
    db_path=Path("~/notes/mdquery.db"),
    cache_dir=Path("~/notes/.cache"),
    notes_dirs=[
        Path("~/Documents/Notes"),
        Path("~/Work/Documentation"),
        Path("~/Research/Papers")
    ]
)

# Start server
await server.run()
```

## Error Handling

All tools return consistent error responses:

```json
{
  "error": {
    "type": "MCPServerError",
    "message": "Query execution failed: syntax error near 'SELCT'",
    "details": {
      "sql": "SELCT * FROM files",
      "suggestion": "Check SQL syntax - did you mean 'SELECT'?"
    }
  }
}
```

### Common Error Types

- **ValidationError**: Invalid parameters or SQL syntax
- **FileNotFoundError**: Specified file or directory doesn't exist
- **DatabaseError**: Database connection or query execution issues
- **PermissionError**: Insufficient file system permissions
- **MCPServerError**: General server errors

## Performance Considerations

### Connection Management

The MCP server maintains persistent database connections for better performance:

- Connection pooling for concurrent requests
- Automatic connection cleanup
- Transaction management for data integrity

### Async Operations

All tools are implemented as async operations:

- Non-blocking query execution
- Concurrent request handling
- Proper resource cleanup

### Memory Management

- Streaming results for large queries
- Configurable result limits
- Automatic garbage collection

## Security

### Local Operation

The MCP server operates entirely locally:
- No network communication
- No data transmission to external servers
- File system access limited to configured directories

### SQL Injection Protection

- Parameterized queries for all user input
- Query validation before execution
- Whitelist approach for allowed operations

### File System Security

- Path validation to prevent directory traversal
- Permission checks before file access
- Sandboxed operation within configured directories

## Troubleshooting

### Common Issues

#### Server Won't Start

```bash
# Check Python path and mdquery installation
python -c "import mdquery.mcp; print('MCP module found')"

# Check database permissions
ls -la ~/.mdquery/

# Start with debug logging
MDQUERY_LOG_LEVEL=DEBUG python -m mdquery.mcp_server
```

#### Query Errors

```bash
# Check database schema
python -c "
from mdquery import CacheManager
cm = CacheManager('~/.mdquery/mdquery.db')
print(cm.get_schema())
"

# Validate SQL syntax
python -c "
from mdquery import QueryEngine, CacheManager
cm = CacheManager('~/.mdquery/mdquery.db')
qe = QueryEngine(cache_manager=cm)
result = qe.execute_query('SELECT COUNT(*) FROM files')
print(result.success, result.error if not result.success else 'OK')
"
```

#### Performance Issues

```bash
# Check database size and indexes
sqlite3 ~/.mdquery/mdquery.db ".schema"
sqlite3 ~/.mdquery/mdquery.db "PRAGMA table_info(files);"

# Analyze query performance
sqlite3 ~/.mdquery/mdquery.db "EXPLAIN QUERY PLAN SELECT * FROM files WHERE tags LIKE '%research%';"
```

### Debug Mode

Enable debug logging for detailed troubleshooting:

```bash
MDQUERY_LOG_LEVEL=DEBUG python -m mdquery.mcp_server
```

Debug output includes:
- SQL query execution details
- File processing information
- Performance metrics
- Error stack traces

## Integration Examples

### Claude Desktop Integration

Once configured, you can ask Claude to:

```
"Query my notes for all files tagged with 'research' from the last month"

"Index my new notes directory and then find similar content to my machine learning paper"

"Generate a research summary for all my AI-related notes and show me the most common topics"

"Analyze the SEO quality of my blog posts and suggest improvements"
```

Claude will automatically use the appropriate MCP tools to fulfill these requests.

### Custom AI Assistant Integration

```python
import asyncio
from mdquery.mcp import MDQueryMCPServer

async def ai_assistant_query(query_text: str):
    server = MDQueryMCPServer()

    # Use fuzzy search to find relevant content
    results = await server.fuzzy_search(
        search_text=query_text,
        threshold=0.6,
        max_results=10
    )

    # Process results for AI assistant
    relevant_files = json.loads(results)
    return [r['file_path'] for r in relevant_files]
```

This MCP server integration makes mdquery's powerful markdown querying capabilities available to any MCP-compatible AI assistant, enabling sophisticated note analysis and research workflows.