# CLI Interface

The mdquery command-line interface provides a powerful way to index and query your markdown files from the terminal.

## Installation

```bash
pip install mdquery
```

## Basic Usage

```bash
# Index your notes
mdquery index /path/to/notes

# Query your notes
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"

# View database schema
mdquery schema
```

## Commands

### `index` - Index Markdown Files

Index markdown files in a directory for querying.

```bash
mdquery index [OPTIONS] PATH
```

**Arguments:**
- `PATH`: Directory path to index

**Options:**
- `--recursive / --no-recursive`: Scan subdirectories (default: recursive)
- `--incremental / --full`: Use incremental indexing (default: incremental)
- `--format [json|table|csv]`: Output format for statistics (default: table)
- `--db-path PATH`: Database file path (default: ~/.mdquery/mdquery.db)
- `--cache-dir PATH`: Cache directory path (default: ~/.mdquery/cache)
- `--verbose / --quiet`: Verbose output (default: normal)

**Examples:**

```bash
# Index current directory recursively
mdquery index .

# Index specific directory with full reindex
mdquery index ~/notes --full

# Index with custom database location
mdquery index ~/notes --db-path ~/custom/notes.db

# Index with JSON output for scripting
mdquery index ~/notes --format json
```

**Output:**
```
Indexing directory: /Users/username/notes
Processing files: 100%|████████████| 45/45 [00:02<00:00, 18.32files/s]

Indexing Statistics:
┌─────────────────┬───────┐
│ Metric          │ Value │
├─────────────────┼───────┤
│ Files Processed │    45 │
│ Files Updated   │     3 │
│ Files Skipped   │    42 │
│ Processing Time │  2.34s│
│ Total Files     │    45 │
└─────────────────┴───────┘
```

### `query` - Execute SQL Queries

Execute SQL queries against your indexed markdown files.

```bash
mdquery query [OPTIONS] SQL
```

**Arguments:**
- `SQL`: SQL query to execute

**Options:**
- `--format [json|csv|table|markdown]`: Output format (default: table)
- `--limit INTEGER`: Limit number of results
- `--db-path PATH`: Database file path
- `--output PATH`: Save results to file
- `--explain`: Show query execution plan

**Examples:**

```bash
# Basic query
mdquery query "SELECT filename, title FROM files LIMIT 10"

# Query with specific format
mdquery query "SELECT * FROM tags" --format csv

# Save results to file
mdquery query "SELECT * FROM files" --output results.json --format json

# Query with limit
mdquery query "SELECT * FROM files" --limit 5

# Show query execution plan
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'" --explain
```

**Common Query Patterns:**

```bash
# Find files by tag
mdquery query "SELECT filename FROM files f JOIN tags t ON f.id = t.file_id WHERE t.tag = 'research'"

# Search content
mdquery query "SELECT f.filename FROM files f JOIN content_fts fts ON f.id = fts.file_id WHERE content_fts MATCH 'machine learning'"

# Recent files
mdquery query "SELECT filename, modified_date FROM files WHERE modified_date > '2024-01-01' ORDER BY modified_date DESC"

# Tag statistics
mdquery query "SELECT tag, COUNT(*) as count FROM tags GROUP BY tag ORDER BY count DESC LIMIT 10"
```

### `schema` - View Database Schema

Display database schema information.

```bash
mdquery schema [OPTIONS] [TABLE]
```

**Arguments:**
- `TABLE`: Specific table to show schema for (optional)

**Options:**
- `--format [json|table|markdown]`: Output format (default: table)
- `--db-path PATH`: Database file path
- `--show-indexes`: Include index information
- `--show-stats`: Include table statistics

**Examples:**

```bash
# Show all tables
mdquery schema

# Show specific table schema
mdquery schema files

# Show schema with indexes
mdquery schema --show-indexes

# Show schema with statistics
mdquery schema --show-stats --format json
```

**Output:**
```
Database Schema:

Table: files
┌─────────────────┬─────────┬─────────────┬─────────────┐
│ Column          │ Type    │ Nullable    │ Primary Key │
├─────────────────┼─────────┼─────────────┼─────────────┤
│ id              │ INTEGER │ False       │ True        │
│ filename        │ TEXT    │ False       │ False       │
│ file_path       │ TEXT    │ False       │ False       │
│ title           │ TEXT    │ True        │ False       │
│ created_date    │ DATETIME│ True        │ False       │
│ modified_date   │ DATETIME│ True        │ False       │
│ word_count      │ INTEGER │ True        │ False       │
└─────────────────┴─────────┴─────────────┴─────────────┘
```

### `analyze` - Content Analysis

Perform advanced content analysis on your markdown files.

```bash
mdquery analyze [OPTIONS] ANALYSIS_TYPE
```

**Arguments:**
- `ANALYSIS_TYPE`: Type of analysis (seo|structure|links|similarity|report)

**Options:**
- `--files PATH`: Comma-separated list of specific files to analyze
- `--format [json|table|markdown]`: Output format (default: table)
- `--db-path PATH`: Database file path
- `--output PATH`: Save results to file
- `--threshold FLOAT`: Similarity threshold for similarity analysis (0.0-1.0)

**Analysis Types:**

#### SEO Analysis
```bash
mdquery analyze seo
mdquery analyze seo --files "blog-post.md,article.md"
```

#### Content Structure Analysis
```bash
mdquery analyze structure
mdquery analyze structure --format json
```

#### Link Relationship Analysis
```bash
mdquery analyze links
mdquery analyze links --output link-report.json
```

#### Similarity Analysis
```bash
mdquery analyze similarity --files "research-paper.md" --threshold 0.4
```

#### Comprehensive Report
```bash
mdquery analyze report
mdquery analyze report --format markdown --output content-report.md
```

### `search` - Advanced Search

Perform advanced search operations including fuzzy search and cross-collection search.

```bash
mdquery search [OPTIONS] SEARCH_TEXT
```

**Arguments:**
- `SEARCH_TEXT`: Text to search for

**Options:**
- `--type [fuzzy|cross-collection|quotes]`: Search type (default: fuzzy)
- `--threshold FLOAT`: Minimum similarity score (default: 0.6)
- `--max-results INTEGER`: Maximum results to return (default: 50)
- `--fields TEXT`: Fields to search in (default: content,title,headings)
- `--collections TEXT`: Collections to search (for cross-collection search)
- `--format [json|table|markdown]`: Output format (default: table)
- `--db-path PATH`: Database file path

**Examples:**

```bash
# Fuzzy search
mdquery search "machine learning algorithms" --threshold 0.7

# Cross-collection search
mdquery search "research methodology" --type cross-collection --collections "papers,notes,drafts"

# Quote extraction
mdquery search "Einstein" --type quotes --format json

# Search specific fields
mdquery search "neural networks" --fields "title,headings" --max-results 20
```

### `research` - Research Tools

Research-focused tools for academic and professional note-taking.

```bash
mdquery research [OPTIONS] COMMAND
```

**Commands:**
- `summary`: Generate research summary
- `filter`: Filter content by research criteria
- `quotes`: Extract quotes with attribution

**Options:**
- `--date-from DATE`: Filter from date (YYYY-MM-DD)
- `--date-to DATE`: Filter to date (YYYY-MM-DD)
- `--topics TEXT`: Filter by topics/tags (comma-separated)
- `--sources TEXT`: Filter by source paths (comma-separated)
- `--authors TEXT`: Filter by authors (comma-separated)
- `--collections TEXT`: Filter by collections/directories (comma-separated)
- `--format [json|table|markdown]`: Output format (default: table)

**Examples:**

```bash
# Generate research summary
mdquery research summary --date-from 2024-01-01 --topics "ai,machine-learning"

# Filter by research criteria
mdquery research filter --authors "John Doe,Jane Smith" --format json

# Extract quotes
mdquery research quotes --sources "research-papers/" --format markdown
```

## Global Options

These options are available for all commands:

- `--help`: Show help message
- `--version`: Show version information
- `--config PATH`: Configuration file path
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Set logging level
- `--no-color`: Disable colored output

## Configuration

### Configuration File

Create a configuration file at `~/.mdquery/config.yaml`:

```yaml
# Default database path
db_path: ~/.mdquery/mdquery.db

# Default cache directory
cache_dir: ~/.mdquery/cache

# Default output format
default_format: table

# Logging configuration
log_level: INFO
log_file: ~/.mdquery/mdquery.log

# Query defaults
default_limit: 100
explain_queries: false

# Indexing defaults
recursive: true
incremental: true
```

### Environment Variables

- `MDQUERY_DB_PATH`: Default database path
- `MDQUERY_CACHE_DIR`: Default cache directory
- `MDQUERY_CONFIG`: Configuration file path
- `MDQUERY_LOG_LEVEL`: Logging level

## Output Formats

### Table Format (Default)

Human-readable table output:
```
┌─────────────────┬─────────────────────┬─────────────┐
│ filename        │ title               │ word_count  │
├─────────────────┼─────────────────────┼─────────────┤
│ research.md     │ Research Notes      │ 1250        │
│ ideas.md        │ Project Ideas       │ 890         │
└─────────────────┴─────────────────────┴─────────────┘
```

### JSON Format

Machine-readable JSON output:
```json
{
  "success": true,
  "data": [
    {
      "filename": "research.md",
      "title": "Research Notes",
      "word_count": 1250
    }
  ],
  "row_count": 1,
  "execution_time": 0.023
}
```

### CSV Format

Comma-separated values for spreadsheet import:
```csv
filename,title,word_count
research.md,Research Notes,1250
ideas.md,Project Ideas,890
```

### Markdown Format

Markdown table format:
```markdown
| filename | title | word_count |
|----------|-------|------------|
| research.md | Research Notes | 1250 |
| ideas.md | Project Ideas | 890 |
```

## Scripting and Automation

### Bash Scripting

```bash
#!/bin/bash

# Index multiple directories
for dir in ~/notes/*/; do
    echo "Indexing $dir"
    mdquery index "$dir"
done

# Generate daily report
mdquery query "
    SELECT
        COUNT(*) as total_files,
        SUM(word_count) as total_words,
        COUNT(DISTINCT tag) as unique_tags
    FROM files f
    LEFT JOIN tags t ON f.id = t.file_id
    WHERE f.modified_date >= date('now', '-1 day')
" --format json > daily_report.json

# Find files without tags
mdquery query "
    SELECT filename
    FROM files f
    WHERE NOT EXISTS (
        SELECT 1 FROM tags t WHERE t.file_id = f.id
    )
" --format csv > untagged_files.csv
```

### Python Integration

```python
import subprocess
import json

def query_notes(sql: str) -> dict:
    """Execute mdquery and return results as dict."""
    result = subprocess.run([
        'mdquery', 'query', sql, '--format', 'json'
    ], capture_output=True, text=True)

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        raise Exception(f"Query failed: {result.stderr}")

# Usage
results = query_notes("SELECT * FROM files LIMIT 5")
for row in results['data']:
    print(f"File: {row['filename']}, Words: {row['word_count']}")
```

## Performance Tips

### Query Optimization

1. **Use LIMIT**: Always limit large result sets
   ```bash
   mdquery query "SELECT * FROM files LIMIT 100"
   ```

2. **Use Indexes**: Query indexed columns for better performance
   ```bash
   # Fast (uses index)
   mdquery query "SELECT * FROM files WHERE file_path = '/path/to/file.md'"

   # Slower (no index)
   mdquery query "SELECT * FROM files WHERE content LIKE '%search%'"
   ```

3. **Use FTS for Content Search**: Use full-text search for content queries
   ```bash
   mdquery query "
       SELECT f.filename
       FROM files f
       JOIN content_fts fts ON f.id = fts.file_id
       WHERE content_fts MATCH 'search terms'
   "
   ```

### Indexing Optimization

1. **Use Incremental Indexing**: Only process changed files
   ```bash
   mdquery index ~/notes --incremental
   ```

2. **Batch Processing**: Index multiple directories in sequence
   ```bash
   mdquery index ~/notes/dir1 && mdquery index ~/notes/dir2
   ```

3. **Monitor Progress**: Use verbose output for large directories
   ```bash
   mdquery index ~/large-notes --verbose
   ```

## Troubleshooting

### Common Issues

#### Database Locked Error
```bash
# Check for other mdquery processes
ps aux | grep mdquery

# Use different database file
mdquery query "SELECT * FROM files" --db-path ~/temp/mdquery.db
```

#### Permission Denied
```bash
# Check file permissions
ls -la ~/.mdquery/

# Create directory if missing
mkdir -p ~/.mdquery
```

#### SQL Syntax Errors
```bash
# Validate SQL syntax
mdquery query "SELECT * FROM files" --explain

# Check available tables
mdquery schema
```

#### Performance Issues
```bash
# Check database size
du -h ~/.mdquery/mdquery.db

# Analyze query performance
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'" --explain
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
mdquery --log-level DEBUG query "SELECT * FROM files"
```

### Getting Help

```bash
# General help
mdquery --help

# Command-specific help
mdquery query --help
mdquery index --help

# Show version
mdquery --version
```

The CLI interface provides a powerful and flexible way to work with your markdown files, whether you're doing quick queries, generating reports, or building automated workflows.