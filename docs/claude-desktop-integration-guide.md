# Claude Desktop MCP Integration Guide for mdquery

## Project Validation Summary

✅ **Project Setup**: mdquery installs successfully with all dependencies  
✅ **CLI Interface**: All commands working (query, index, schema, etc.)  
✅ **MCP Server**: Server initializes with proper configuration  
✅ **Database System**: SQLite with FTS5 integration functional  
✅ **Tag Analysis Engine**: Comprehensive tag analysis tools available  
✅ **Documentation**: Aligned with actual codebase implementation  

## Overview

This guide provides step-by-step instructions for integrating mdquery's MCP server with Claude Desktop to analyze your Obsidian vault and generate comprehensive topic-based reports from tagged content.

**Key Capabilities Validated:**
- SQL queries against indexed markdown files
- Comprehensive tag analysis with topic grouping
- Advanced content analysis and insight extraction  
- Fuzzy search and cross-collection querying
- Research-focused content filtering and summarization

## Prerequisites

- **Python 3.8+** installed on your system
- **Claude Desktop** application 
- **Obsidian vault** with tagged notes (or any markdown collection)
- **Terminal/Command line** access
- **Minimum 100MB disk space** for database and cache

## Step 1: Install mdquery

### 1.1 Download and Install

```bash
# Navigate to project directory
cd /Users/eristoddle/Dropbox\ \(Maestral\)/python/mdquery

# Install dependencies (fixed requirements.txt)
pip install -r requirements.txt

# Install mdquery in development mode
pip install -e .

# Verify installation
mdquery --help
```

**Expected Output:**
```
Usage: mdquery [OPTIONS] COMMAND [ARGS]...

mdquery - Universal markdown querying tool with SQL-like syntax.
```

### 1.2 Verify MCP Server

```bash
# Test MCP server help
python -m mdquery.mcp_server --help
```

**Expected Output:**
```
usage: mcp_server.py [-h] [--notes-dir NOTES_DIR] [--db-path DB_PATH] [--cache-dir CACHE_DIR] [--no-auto-index] [--config CONFIG] [--debug]

mdquery MCP Server
```

## Step 2: Prepare Your Obsidian Vault

### 2.1 Identify Your Vault Location

Common locations:
- **macOS**: `~/Documents/ObsidianVault` or `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/YourVault`
- **Windows**: `%USERPROFILE%\Documents\ObsidianVault`
- **Linux**: `~/Documents/ObsidianVault`

### 2.2 Verify Tag Structure

Ensure your notes use consistent tagging:
```markdown
---
tags: [research, ai, machine-learning]
---

# Your content with #inline-tags
```

## Step 3: Initialize mdquery Database

### 3.1 Index Your Vault

```bash
# Set your vault path
export VAULT_PATH="/path/to/your/obsidian/vault"

# Index the vault
mdquery index "$VAULT_PATH" --recursive

# Verify indexing
mdquery schema --directory "$VAULT_PATH"
```

### 3.2 Test Basic Queries

```bash
# Count total files
mdquery query "SELECT COUNT(*) as total_files FROM files" --directory "$VAULT_PATH"

# List files with specific tag
mdquery query "SELECT path, title FROM files WHERE tags LIKE '%your-tag%'" --directory "$VAULT_PATH"
```

## Step 4: Configure Claude Desktop

### 4.1 Create MCP Configuration

**Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/obsidian/vault"
      }
    }
  }
}
```

### 4.2 Alternative: Advanced Configuration

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/your/obsidian/vault",
        "MDQUERY_DB_PATH": "/path/to/vault/.mdquery/mdquery.db",
        "MDQUERY_CACHE_DIR": "/path/to/vault/.mdquery/cache",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true"
      }
    }
  }
}
```

### 4.3 Restart Claude Desktop

Completely quit and restart Claude Desktop for the MCP configuration to take effect.

## Step 5: Available MCP Tools

### Core Analysis Tools

#### `comprehensive_tag_analysis`
**Purpose**: Generate detailed analysis of tagged content with topic grouping  
**Parameters**:
- `tag_patterns`: Comma-separated tag patterns (supports wildcards like "ai/*")
- `grouping_strategy`: "semantic", "tag-hierarchy", or "temporal" 
- `include_actionable`: Include practical recommendations (default: true)
- `include_theoretical`: Include conceptual insights (default: true)
- `remove_fluff`: Filter out low-quality content (default: true)
- `min_content_quality`: Minimum quality score 0.0-1.0 (default: 0.3)

#### `query_markdown`
**Purpose**: Execute SQL queries against indexed files  
**Parameters**:
- `sql`: SQL query string
- `format`: Output format (json, csv, table, markdown)

#### `fuzzy_search`
**Purpose**: Find content similar to search text  
**Parameters**:
- `search_text`: Text to search for
- `threshold`: Similarity threshold 0.0-1.0 (default: 0.6)
- `max_results`: Maximum results (default: 50)
- `search_fields`: Fields to search (content,title,headings)

#### `get_schema`
**Purpose**: Retrieve database schema information  
**Parameters**:
- `table`: Specific table name (optional)

#### `index_directory`
**Purpose**: Index markdown files in directory  
**Parameters**:
- `path`: Directory path to index
- `recursive`: Include subdirectories (default: true)
- `incremental`: Use incremental indexing (default: true)

## Step 6: Optimized Claude Desktop Prompts

### Primary Analysis Prompt

```markdown
I need a comprehensive topic-based analysis of my research notes. Please help me analyze documents tagged with [YOUR_TAG] and create a detailed guidebook organized by topics.

**Requirements:**
1. **No summaries or fluff** - I want actionable content only
2. **Complete tutorial steps** - Include all steps for recreation if tutorials found
3. **Topic organization** - Break content into logical topic groups  
4. **Comprehensive coverage** - This is for deep research, not quick overview

**Analysis Steps:**
1. First, use `comprehensive_tag_analysis` with:
   - Tag pattern: "[YOUR_TAG]"
   - Grouping strategy: "semantic" 
   - Remove fluff: true
   - Include actionable: true
   - Include theoretical: true

2. Then, for each major topic identified:
   - Extract actionable items, procedures, and methods
   - Identify complete tutorials with step-by-step instructions
   - Find relevant examples and case studies
   - Note important references and resources

3. Finally, organize everything into a structured guidebook with:
   - Topic-based sections
   - Actionable subsections within each topic
   - Complete tutorial reproductions
   - Reference materials and links

**My tag pattern**: [YOUR_TAG]
**Expected output**: A comprehensive guidebook for practical implementation

Please start by analyzing my tagged content and proceed with detailed extraction and organization.
```

### Deep Dive Analysis Prompt

```markdown
Based on the initial analysis, I want to dive deeper into [SPECIFIC_TOPIC]. Please:

1. Use `query_markdown` to find all content related to this topic:
   ```sql
   SELECT path, title, tags, content FROM files_with_content 
   WHERE tags LIKE '%[TOPIC_TAG]%' OR content LIKE '%[TOPIC_KEYWORDS]%'
   ```

2. Use `fuzzy_search` to find related content:
   - Search text: "[TOPIC_DESCRIPTION]"
   - Threshold: 0.7
   - Fields: "content,title"

3. Extract and compile:
   - Step-by-step procedures and tutorials
   - Best practices and methodologies  
   - Actionable resources and tools
   - Complete code examples or commands

4. Create a focused sub-guidebook for this topic with practical implementation focus.

Use both SQL queries and content analysis tools for comprehensive coverage.
```

### Tutorial Extraction Prompt

```markdown
I noticed references to tutorials in the analysis. Please extract actionable tutorial content:

1. Use `comprehensive_tag_analysis` with:
   - Tag patterns: "[YOUR_TAG],tutorial,guide,howto"
   - Include actionable: true
   - Remove fluff: true

2. For each tutorial found, extract:
   - Complete step-by-step procedures
   - Prerequisites and requirements
   - Code examples or commands
   - Expected outcomes

3. Use `fuzzy_search` to find similar tutorials:
   - Search for "tutorial", "step by step", "how to"
   - Include all actionable guides

Format as complete, standalone guides I can follow without referring to original sources.
```

## Step 7: Testing Your Setup

### 7.1 Basic Functionality Test

In Claude Desktop, try:

```
Please use the get_schema tool to show me what data is available in my notes database.
```

### 7.2 Tag Analysis Test

```
Please use comprehensive_tag_analysis to analyze content tagged with "research" using semantic grouping.
```

### 7.3 Query Test

```
Please use query_markdown to show me the 10 most recent files: 
"SELECT path, title, created_date FROM files ORDER BY created_date DESC LIMIT 10"
```

## Troubleshooting

### Common Issues

**MCP Connection Problems:**
1. Verify Claude Desktop configuration JSON syntax
2. Check file paths in configuration
3. Ensure Python is in system PATH

**Database Issues:**
1. Re-index your vault: `mdquery index /path/to/vault --rebuild`
2. Check permissions on vault directory
3. Verify markdown files are present

**Performance Issues:**
1. Increase cache size in configuration
2. Use incremental indexing for large vaults
3. Monitor system resources during analysis

**Empty Results:**
1. Verify tags exist: `mdquery query "SELECT DISTINCT tag FROM tags LIMIT 20"`
2. Check tag format (ensure consistent tagging)
3. Try fuzzy search for broader matching

### Error Recovery

If indexing fails:
```bash
# Clear existing index
rm -rf /path/to/vault/.mdquery

# Rebuild from scratch  
mdquery index /path/to/vault --rebuild
```

If MCP server fails to start:
1. Check Python dependencies: `pip list | grep mcp`
2. Verify file permissions
3. Try running server manually for debugging

## Expected Output Format

Your comprehensive analysis will produce:

1. **Topic Overview**: High-level categorization of tagged content
2. **Detailed Topic Sections**: In-depth analysis of each area
3. **Actionable Items**: Specific procedures, methods, and techniques
4. **Complete Tutorials**: Step-by-step guides extracted from notes
5. **Resource Compilation**: Tools, links, and references by topic
6. **Cross-References**: Connections between related concepts

## Advanced Usage

### Multiple Vaults

Configure separate MCP servers for different vaults:

```json
{
  "mcpServers": {
    "mdquery-research": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/research/vault"
      }
    },
    "mdquery-personal": {
      "command": "python", 
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/path/to/personal/vault"
      }
    }
  }
}
```

### Performance Optimization

For large vaults (1000+ files):

```json
{
  "env": {
    "MDQUERY_NOTES_DIR": "/path/to/vault",
    "MDQUERY_PERFORMANCE_MODE": "high",
    "MDQUERY_CONCURRENT_QUERIES": "5",
    "MDQUERY_CACHE_TTL": "120"
  }
}
```

## Conclusion

This integration enables you to leverage Claude Desktop's natural language interface with mdquery's powerful markdown analysis capabilities. The result is an intelligent research assistant that can analyze your Obsidian vault and generate actionable, comprehensive guides from your tagged content.

**Key Benefits:**
- No fluff, actionable content extraction
- Complete tutorial preservation and reproduction
- Semantic topic organization and cross-referencing  
- Scalable to large note collections
- Natural language querying interface

Your setup is now ready to transform your tagged research notes into organized, actionable knowledge resources.