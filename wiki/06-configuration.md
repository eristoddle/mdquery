# Configuration

## Overview

The mdquery system uses a simplified configuration approach that prioritizes ease of use while maintaining flexibility for advanced users. The configuration system is designed around a "path-first" philosophy, where users only need to specify their notes directory, and the system automatically handles the rest with intelligent defaults.

## Environment Variables

### Supported Environment Variables

mdquery supports several environment variables for configuration:

- **MDQUERY_NOTES_DIR**: Directory containing markdown files
- **MDQUERY_DB_PATH**: Path to SQLite database file
- **MDQUERY_CACHE_DIR**: Directory for cache files
- **MDQUERY_ENABLE_WIKILINKS**: Enable wikilink parsing (true/false)
- **MDQUERY_ENABLE_NESTED_TAGS**: Enable nested tag support (true/false)
- **MDQUERY_LOG_LEVEL**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **MDQUERY_QUERY_TIMEOUT**: Default query timeout in seconds
- **MDQUERY_MAX_RESULTS**: Maximum number of query results

### Setting Environment Variables

#### Unix-like Systems (Linux/macOS)

In Bash or similar shells:

```bash
export MDQUERY_NOTES_DIR="/Users/username/Documents/Notes"
export MDQUERY_DB_PATH="/Users/username/.mdquery/mdquery.db"
export MDQUERY_CACHE_DIR="/Users/username/.mdquery/cache"
```

To make these settings persistent, add them to your shell profile:

```bash
echo 'export MDQUERY_NOTES_DIR="/Users/username/Documents/Notes"' >> ~/.zshrc
source ~/.zshrc
```

#### Windows Systems

In Command Prompt:
```cmd
set MDQUERY_NOTES_DIR=C:\Users\username\Documents\Notes
set MDQUERY_DB_PATH=C:\Users\username\.mdquery\mdquery.db
set MDQUERY_CACHE_DIR=C:\Users\username\.mdquery\cache
```

In PowerShell:
```powershell
$env:MDQUERY_NOTES_DIR = "C:\Users\username\Documents\Notes"
$env:MDQUERY_DB_PATH = "C:\Users\username\.mdquery\mdquery.db"
$env:MDQUERY_CACHE_DIR = "C:\Users\username\.mdquery\cache"
```

To set permanent environment variables in Windows:
```powershell
[Environment]::SetEnvironmentVariable("MDQUERY_NOTES_DIR", "C:\Users\username\Documents\Notes", "User")
```

### Temporary Session Variables

For temporary overrides during a single session:

```bash
# Run command with temporary environment variables
MDQUERY_NOTES_DIR="/tmp/test_notes" MDQUERY_DB_PATH="/tmp/test.db" mdquery index

# Or using env command
env MDQUERY_NOTES_DIR="/tmp/test_notes" MDQUERY_DB_PATH="/tmp/test.db" mdquery query "SELECT * FROM files"
```

## Configuration File

### File Locations

mdquery looks for configuration files in the following order:

1. `.mdquery/config.json` in the current directory
2. `~/.mdquery/config.json` in the user's home directory
3. Environment variables
4. Built-in defaults

### Configuration File Format

Configuration files use JSON format:

```json
{
  "notes_dir": "/path/to/notes",
  "db_path": "/path/to/database.db",
  "cache_dir": "/path/to/cache",
  "auto_index": true,
  "note_system_type": "obsidian",
  "index": {
    "recursive": true,
    "incremental": true,
    "include_patterns": ["*.md", "*.markdown"],
    "exclude_patterns": [".git", "node_modules", ".obsidian"]
  },
  "query": {
    "format": "table",
    "timeout": 30.0,
    "limit": null,
    "max_results": 1000
  },
  "database": {
    "directory": ".mdquery",
    "optimize_on_close": true
  },
  "cache": {
    "enabled": true,
    "max_size_mb": 100,
    "ttl_hours": 24
  },
  "parsing": {
    "enable_wikilinks": true,
    "enable_nested_tags": true,
    "extract_headings": true,
    "process_frontmatter": true
  },
  "logging": {
    "level": "INFO",
    "file": null,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### Creating Configuration Files

#### Using SimplifiedConfig

```python
from mdquery.config import SimplifiedConfig

# Create and save configuration
config = SimplifiedConfig(
    notes_dir="/path/to/notes",
    db_path="/custom/path/database.db",
    cache_dir="/custom/path/cache"
)
config.save_config()
```

#### Manual Creation

Create a `.mdquery/config.json` file in your notes directory or home directory with the desired settings.

## MCP Server Configuration

### Basic MCP Configuration

For MCP server setup, create a dedicated configuration file:

```json
{
  "notes_dir": "/path/to/notes",
  "db_path": "/path/to/mdquery.db",
  "cache_dir": "/path/to/cache",
  "mcp": {
    "host": "localhost",
    "port": 8080,
    "auto_index": true,
    "enable_cors": false,
    "max_concurrent_requests": 10,
    "request_timeout": 30
  },
  "ai_integration": {
    "adaptive_formatting": true,
    "response_format": "json",
    "include_metadata": true,
    "max_response_size": 10000
  }
}
```

### Starting MCP Server with Configuration

```bash
# Start server with configuration file
mdquery mcp --config mcp_config.json

# Start server with environment variables
MDQUERY_NOTES_DIR=/path/to/notes mdquery mcp

# Start server with command-line options
mdquery mcp --notes-dir /path/to/notes --port 8080
```

## Configuration Loading Order

The configuration system follows a specific precedence order:

1. **Command-line arguments**: Highest precedence
2. **Environment variables**: Medium-high precedence
3. **Local configuration file**: Medium precedence
4. **Global configuration file**: Medium-low precedence
5. **Built-in defaults**: Lowest precedence

This hierarchy ensures that users can override settings at different levels, with command-line arguments providing the most immediate control.

## Performance and Indexing Configuration

### Indexing Options

```json
{
  "index": {
    "recursive": true,
    "incremental": true,
    "parallel_processing": true,
    "max_workers": 4,
    "chunk_size": 100,
    "include_patterns": ["*.md", "*.markdown", "*.txt"],
    "exclude_patterns": [
      ".git", "node_modules", ".obsidian",
      "*.tmp", "*.bak", ".DS_Store"
    ],
    "follow_symlinks": false,
    "max_file_size_mb": 50
  }
}
```

### Cache Configuration

```json
{
  "cache": {
    "enabled": true,
    "type": "file",
    "directory": ".mdquery/cache",
    "max_size_mb": 100,
    "ttl_hours": 24,
    "compress": true,
    "cleanup_on_start": false
  }
}
```

### Database Optimization

```json
{
  "database": {
    "directory": ".mdquery",
    "filename": "mdquery.db",
    "optimize_on_close": true,
    "vacuum_on_start": false,
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": 10000,
    "temp_store": "MEMORY"
  }
}
```

## Troubleshooting Configuration

### Common Issues

1. **Configuration not found**: Check file paths and permissions
2. **Invalid JSON**: Validate JSON syntax
3. **Permission errors**: Ensure write access to config directories
4. **Environment variables not recognized**: Check variable names and values

### Debugging Configuration

```bash
# Show current configuration
mdquery config show

# Validate configuration file
python -c "import json; json.load(open('.mdquery/config.json'))"

# Check environment variables
env | grep MDQUERY
```

### Configuration Validation

The system automatically validates configuration:

- **Path validation**: Ensures directories exist or can be created
- **Type checking**: Validates data types for all settings
- **Range checking**: Ensures numeric values are within valid ranges
- **Dependency checking**: Validates that required dependencies are available

### Default Configuration

If no configuration is provided, mdquery uses these defaults:

```json
{
  "notes_dir": ".",
  "db_path": ".mdquery/mdquery.db",
  "cache_dir": ".mdquery/cache",
  "auto_index": true,
  "note_system_type": "auto_detect",
  "index": {
    "recursive": true,
    "incremental": true
  },
  "query": {
    "format": "table",
    "timeout": 30.0,
    "limit": null
  }
}
```