# Quick Start Guide

## Minimum Setup Requirements

To get started with mdquery, you need:
- A directory containing markdown files
- Python 3.8+ with mdquery installed
- Basic familiarity with SQL syntax (optional but helpful)

## Initializing Configuration

### Using SimplifiedConfig (Recommended)

The simplest approach uses the `SimplifiedConfig` class which requires only a notes directory path:

```python
from mdquery.config import SimplifiedConfig

# Initialize configuration with your notes directory
config = SimplifiedConfig(notes_dir="/path/to/your/notes")
```

This configuration automatically:
- Creates a `.mdquery` directory within your notes folder
- Sets up a database file at `.mdquery/mdquery.db`
- Creates a cache directory at `.mdquery/cache`
- Detects your note system type (Obsidian, Joplin, etc.)
- Enables auto-indexing by default

### Custom Configuration

For custom paths, you can specify database and cache locations:

```python
config = SimplifiedConfig(
    notes_dir="/path/to/notes",
    db_path="/custom/path/database.db",
    cache_dir="/custom/path/cache",
    auto_index=False
)
```

### Saving and Loading Configuration

```python
# Save configuration
config.save_config()

# Load configuration from file
loaded_config = SimplifiedConfig.load_config("/path/to/config.json")
```

## Basic Workflow

### 1. Index Your Notes

First, index your markdown files:

```bash
# Index current directory recursively (default behavior)
mdquery index

# Index specific directory
mdquery index /path/to/your/notes

# Index with specific options
mdquery index /path/to/notes --recursive
```

### 2. Query Your Notes

Once indexed, you can query your notes:

```bash
# Find all files with research tag
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"

# Find files modified after a specific date
mdquery query "SELECT filename, modified_date FROM files WHERE modified_date > '2024-01-01'"

# Search for content containing specific text
mdquery query "SELECT filename FROM files WHERE content MATCH 'knowledge management'"
```

### 3. Explore the Schema

Understand what data is available:

```bash
# Show all tables and views
mdquery schema

# Show specific table structure
mdquery schema --table files

# Show database statistics
mdquery schema --stats
```

## Available Tables and Fields

### files table
Core file metadata:
- `id`: Unique identifier
- `path`: File path
- `filename`: File name
- `directory`: Directory path
- `modified_date`: Last modified date
- `created_date`: Creation date
- `file_size`: File size in bytes
- `word_count`: Number of words
- `heading_count`: Number of headings

### frontmatter table
Key-value pairs from YAML/TOML frontmatter:
- `file_id`: Reference to files table
- `key`: Frontmatter key
- `value`: Frontmatter value
- `value_type`: Data type (string, array, etc.)

### tags table
Extracted tags:
- `file_id`: Reference to files table
- `tag`: Tag name
- `source`: Source of tag (frontmatter, content, etc.)

### links table
Extracted links:
- `file_id`: Reference to files table
- `link_text`: Display text of link
- `link_target`: Target URL or file
- `link_type`: Type of link
- `is_internal`: Whether link is internal

## Common Query Patterns

### Finding Notes by Tags

```sql
-- Exact tag match
SELECT filename FROM files
JOIN tags ON files.id = tags.file_id
WHERE tags.tag = 'research';

-- Pattern matching
SELECT filename FROM files
JOIN tags ON files.id = tags.file_id
WHERE tags.tag LIKE 'research%';
```

### Content Search

```sql
-- Full-text search
SELECT filename FROM files WHERE content MATCH 'knowledge management';

-- Search in titles
SELECT filename FROM files WHERE content MATCH 'title:knowledge';
```

### Metadata Queries

```sql
-- Find files with specific frontmatter
SELECT f.filename, fm.value as title
FROM files f
JOIN frontmatter fm ON f.id = fm.file_id
WHERE fm.key = 'title';
```

## Next Steps

- Explore the [Command Reference](04-command-reference.md) for detailed command options
- Learn about [Query Syntax](05-query-syntax-guide.md) for advanced querying
- Set up [Configuration](06-configuration.md) for your specific needs
- Check [Supported Markdown Systems](07-supported-markdown-systems.md) for system-specific features