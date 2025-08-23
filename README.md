# mdquery

Universal markdown querying tool with SQL-like syntax for searching and analyzing markdown files across different note-taking systems and static site generators.

## Project Structure

```
mdquery/
├── __init__.py              # Package initialization and exports
├── models.py                # Core data models (QueryResult, FileMetadata, ParsedContent)
├── indexer.py               # File indexing engine
├── query.py                 # SQL query engine
├── cache.py                 # Cache management system
├── cli.py                   # Command-line interface
├── mcp.py                   # MCP server interface
└── parsers/
    ├── __init__.py          # Parsers package initialization
    ├── frontmatter.py       # Frontmatter parser
    ├── markdown.py          # Markdown content parser
    ├── tags.py              # Tag extraction parser
    └── links.py             # Link extraction parser
```

## Installation

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Query markdown files
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"

# Index a directory
mdquery index /path/to/notes --recursive

# View schema
mdquery schema --table files
```

### Python API

```python
from mdquery import QueryResult, FileMetadata, ParsedContent
from mdquery.query import QueryEngine
from mdquery.indexer import Indexer

# Initialize components
indexer = Indexer()
query_engine = QueryEngine()

# Index files and query
indexer.index_directory("/path/to/notes")
result = query_engine.execute_query("SELECT * FROM files")
```

## Development

This project follows a structured implementation plan. See `.kiro/specs/mdquery/tasks.md` for the complete task list and implementation order.

## Requirements

- Python 3.8+
- SQLite3 (included with Python)
- Dependencies listed in requirements.txt

## License

MIT License