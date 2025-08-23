# mdquery

Universal markdown querying tool with SQL-like syntax for searching and analyzing markdown files across different note-taking systems and static site generators.

## Table of Contents

- [mdquery](#mdquery)
  - [Table of Contents](#table-of-contents)
  - [🚀 Quick Start](#-quick-start)
  - [📚 Documentation](#-documentation)
  - [Project Structure](#project-structure)
  - [Usage](#usage)
    - [Command Line Interface](#command-line-interface)
    - [Python API](#python-api)
  - [✨ Key Features](#-key-features)
  - [🔍 Quick Examples](#-quick-examples)
    - [Find Research Notes](#find-research-notes)
    - [Content Analysis](#content-analysis)
    - [Cross-Reference Analysis](#cross-reference-analysis)
  - [📋 Supported Markdown Systems](#-supported-markdown-systems)
  - [🧪 Development](#-development)
    - [Running Tests](#running-tests)
  - [Requirements](#requirements)
  - [Contributing](#contributing)
  - [🆘 Need Help?](#-need-help)
  - [📄 License](#-license)

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt
pip install -e .

# Index your notes
mdquery index /path/to/your/notes

# Query your notes
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"
```

## 📚 Documentation

| Resource | Description |
|----------|-------------|
| **[📖 Complete Documentation](docs/README.md)** | Full documentation hub with all guides |
| **[🎯 User Guide](docs/user-guide/README.md)** | Getting started, installation, and usage |
| **[📝 Query Syntax](docs/user-guide/query-syntax.md)** | Complete SQL syntax reference and examples |
| **[🔧 API Reference](docs/api/README.md)** | Developer API documentation |
| **[💡 Examples](docs/user-guide/examples/README.md)** | Real-world usage examples and workflows |
| **[⚡ Best Practices](docs/user-guide/best-practices.md)** | Performance tips and optimization |

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

## ✨ Key Features

- **Universal Compatibility**: Works with Obsidian, Joplin, Jekyll, and generic markdown
- **SQL-Like Queries**: Familiar syntax for powerful searches and analysis
- **Full-Text Search**: Fast content search with SQLite FTS5
- **Rich Metadata**: Query frontmatter, tags, links, and content structure
- **High Performance**: Efficient indexing and caching for large collections
- **Multiple Interfaces**: CLI tool and MCP server for AI integration

## 🔍 Quick Examples

### Find Research Notes
```sql
SELECT filename, tags FROM files
WHERE tags LIKE '%research%'
ORDER BY modified_date DESC;
```

### Content Analysis
```sql
SELECT tag, COUNT(*) as usage FROM tags
GROUP BY tag
ORDER BY usage DESC
LIMIT 10;
```

### Cross-Reference Analysis
```sql
SELECT f.filename, COUNT(l.link_target) as outgoing_links
FROM files f
JOIN links l ON f.id = l.file_id
WHERE l.is_internal = 1
GROUP BY f.id
ORDER BY outgoing_links DESC;
```

## 📋 Supported Markdown Systems

| System | Wikilinks | Nested Tags | Frontmatter | Collections |
|--------|-----------|-------------|-------------|-------------|
| **Obsidian** | ✅ `[[Page]]` | ✅ `#parent/child` | ✅ YAML | ✅ Folders |
| **Joplin** | ❌ | ❌ | ✅ Metadata | ✅ Notebooks |
| **Jekyll** | ❌ | ❌ | ✅ YAML | ✅ `_posts`, `_pages` |
| **Generic** | ❌ | ❌ | ✅ YAML | ✅ Directories |

## 🧪 Development

This project follows a structured implementation plan. See `.kiro/specs/mdquery/tasks.md` for the complete task list and implementation order.

### Running Tests

```bash
# Run all tests
python tests/run_comprehensive_tests.py

# Generate performance test data (1000+ files)
python tests/generate_performance_data.py

# Run specific test categories
python -m pytest tests/test_format_compatibility.py -v
```

## Requirements

- Python 3.8+
- SQLite3 (included with Python)
- Dependencies listed in requirements.txt

## Contributing

See the [documentation](docs/README.md) for complete guides on:
- [API Reference](docs/api/README.md) for developers
- [Examples](docs/user-guide/examples/README.md) for usage patterns
- [Best Practices](docs/user-guide/best-practices.md) for optimization

## 🆘 Need Help?

| Question | Resource |
|----------|----------|
| **How do I get started?** | [User Guide](docs/user-guide/README.md) |
| **What queries can I write?** | [Query Syntax Guide](docs/user-guide/query-syntax.md) |
| **How do I use the Python API?** | [API Reference](docs/api/README.md) |
| **Can you show me real examples?** | [Examples Collection](docs/user-guide/examples/README.md) |
| **How do I optimize performance?** | [Best Practices](docs/user-guide/best-practices.md) |
| **Does it work with my markdown system?** | [Supported Systems](#-supported-markdown-systems) |

## 📄 License

MIT License