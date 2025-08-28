# Command Reference

## Overview

mdquery provides several commands for indexing, querying, and managing markdown repositories. Each command has specific options and use cases.

## index Command

### Purpose
The `index` command scans and processes markdown files in a directory, extracting metadata and content for querying.

### Syntax
```bash
mdquery index [DIRECTORY] [OPTIONS]
```

### Arguments
- `DIRECTORY`: Path to directory containing markdown files (default: current directory)

### Options
- `--recursive / --no-recursive`: Include subdirectories (default: enabled)
- `--incremental / --full`: Incremental vs full reindex (default: incremental)
- `--force`: Force reindexing even if files haven't changed
- `--directory`: Directory for index files (default: current directory)

### Usage Examples

```bash
# Index current directory recursively (default behavior)
mdquery index

# Index specific directory non-recursively
mdquery index ./notes --no-recursive

# Perform full reindex of blog directory
mdquery index ./blog --full --force

# Incrementally index research directory
mdquery index ./research --incremental
```

### Practical Examples

**Indexing an Obsidian Vault:**
```bash
mdquery index ~/Documents/ObsidianVault --recursive
```

**Indexing a Jekyll Site:**
```bash
mdquery index ~/Sites/my-blog --recursive
```

## query Command

### Purpose
Execute SQL-like queries against the indexed markdown database.

### Syntax
```bash
mdquery query "SQL_QUERY" [OPTIONS]
```

### Arguments
- `SQL_QUERY`: SQL query to execute (required)

### Options
- `--format`: Output format (json, csv, table, markdown) - default: table
- `--directory`: Directory containing the index (default: current directory)
- `--limit`: Maximum number of results to return
- `--timeout`: Query timeout in seconds (default: 30)

### Usage Examples

```bash
# Basic queries
mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"
mdquery query "SELECT filename, modified_date FROM files ORDER BY modified_date DESC"

# With formatting options
mdquery query "SELECT * FROM files" --format json
mdquery query "SELECT * FROM files" --format csv

# With limits and timeout
mdquery query "SELECT * FROM files" --limit 10 --timeout 60
```

### Error Conditions and Validation

The command implements comprehensive validation:
- Checks for existing index in the specified directory
- Validates SQL syntax using SQLite's EXPLAIN command
- Blocks dangerous SQL operations (DROP, DELETE, INSERT, etc.)
- Enforces single-statement queries (no semicolons)
- Implements query timeout protection
- Validates table and view references against allowed list

## schema Command

### Purpose
Display information about the database structure, helping users understand available tables, columns, and relationships.

### Syntax
```bash
mdquery schema [OPTIONS]
```

### Options
- `--table/-t`: Show schema for specific table or view
- `--directory/-d`: Directory containing the index (default: current directory)
- `--stats`: Show database statistics
- `--verbose/-v`: Show additional details including indexes

### Usage Examples

```bash
# Show all tables and views
mdquery schema

# Show specific table structure
mdquery schema --table files

# Show database statistics
mdquery schema --stats

# Show detailed schema with indexes (verbose)
mdquery schema --verbose
```

### Output Formats
The command provides formatted text output:
- Table overview with row counts
- Detailed column information with data types and constraints
- Statistics about tables, views, and indexes
- SQL definition for views when requested

## mcp Command

### Purpose
Start the MCP (Model Communication Protocol) server for AI assistant integration.

### Syntax
```bash
mdquery mcp [OPTIONS]
```

### Options
- `--notes-dir`: Directory containing markdown files
- `--db-path`: Path to SQLite database file
- `--cache-dir`: Directory for cache files
- `--config`: Configuration file path
- `--host`: Server host (default: localhost)
- `--port`: Server port (default: 8080)

### Usage Examples

```bash
# Start server with notes directory
mdquery mcp --notes-dir ~/Documents/ObsidianVault

# Start server with custom database path
mdquery mcp --notes-dir ~/Documents/Notes --db-path ~/custom/db.sqlite

# Start server with configuration file
mdquery mcp --config mcp_config.json
```

## config Command

### Purpose
Manage configuration settings for mdquery.

### Syntax
```bash
mdquery config [SUBCOMMAND] [OPTIONS]
```

### Subcommands
- `show`: Display current configuration
- `set`: Set configuration value
- `get`: Get configuration value
- `init`: Initialize configuration file

### Usage Examples

```bash
# Show current configuration
mdquery config show

# Set configuration value
mdquery config set query.format table

# Get configuration value
mdquery config get query.format

# Initialize configuration file
mdquery config init
```

## Error Handling and Exit Codes

### Exit Codes
- `0`: Success
- `1`: General error
- `2`: Directory not found or index missing
- `3`: Configuration error
- `4`: Database error

### Validation Checks
Each command performs specific validation:
- **index**: Directory existence, write permissions, system resources
- **query**: Index existence, SQL syntax, security constraints, timeout
- **schema**: Index existence, valid table name
- **mcp**: Server connectivity, valid configuration
- **config**: Valid keys, proper value types, file accessibility

## Configuration Integration

mdquery commands integrate with configuration settings to provide customizable behavior and defaults.

### Configuration Hierarchy
Settings follow a precedence hierarchy:
1. Command-line flags (highest precedence)
2. Local configuration (.mdquery/config.json in project)
3. Global configuration (~/.mdquery/config.json)
4. Built-in defaults (lowest precedence)

### Configuration File Structure
Configuration files use JSON format:

```json
{
  "index": {
    "recursive": true,
    "incremental": true
  },
  "query": {
    "format": "table",
    "timeout": 30.0,
    "limit": null
  },
  "database": {
    "directory": ".mdquery"
  }
}
```