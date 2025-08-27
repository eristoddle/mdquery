# MCP Integration Guide

This guide covers how to use mdquery with AI assistants through the Model Context Protocol (MCP) server integration.

## What is MCP?

The Model Context Protocol (MCP) is a standard for connecting AI assistants to external tools and data sources. mdquery's MCP server allows AI assistants like Claude to directly query and analyze your markdown files.

## Benefits of MCP Integration

- **Natural Language Queries**: Ask questions in plain English instead of writing SQL
- **Intelligent Analysis**: AI can perform complex analysis and generate insights
- **Automated Workflows**: AI can chain multiple operations together
- **Context Awareness**: AI understands your note structure and relationships
- **Multi-Assistant Support**: Works seamlessly with Claude, GPT, and other AI assistants
- **Automatic Optimization**: Built-in performance optimization and query enhancement
- **Error Recovery**: Graceful failure handling with automatic recovery mechanisms
- **Concurrent Access**: Multiple AI assistants can access your notes simultaneously

## Setup and Configuration

### Prerequisites

- Python 3.8 or higher
- mdquery installed with MCP support
- MCP-compatible AI assistant (Claude Desktop, ChatGPT with MCP, etc.)
- Minimum 100MB available disk space for database and cache

### Installation

```bash
# Install mdquery with MCP support
pip install mdquery[mcp]

# Verify MCP server works
python -m mdquery.mcp_server --help
```

### Claude Desktop Configuration

Add mdquery to your Claude Desktop configuration file:

**Location**: `~/.claude/claude_desktop_config.json`

#### Simplified Configuration (Recommended)

**For most users - just specify your notes directory:**

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/Notes"
      }
    }
  }
}
```

**Advanced Configuration (Full Control):**

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/Notes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/notes.db",
        "MDQUERY_CACHE_DIR": "/Users/username/.mdquery/cache",
        "MDQUERY_PERFORMANCE_MODE": "high",
        "MDQUERY_AUTO_OPTIMIZE": "true",
        "MDQUERY_CONCURRENT_QUERIES": "5"
      }
    }
  }
}
```

#### Multiple Notes Directories (Separate Servers)

```json
{
  "mcpServers": {
    "mdquery-personal": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/PersonalNotes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/personal.db"
      }
    },
    "mdquery-work": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Work/Documentation",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/work.db"
      }
    },
    "mdquery-research": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Research/Papers",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/research.db"
      }
    }
  }
}
```

#### Combined Multiple Directories (Single Server)

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server", "--notes-dir", "/Users/username/Documents/Notes,/Users/username/Work/Docs,/Users/username/Research"],
      "env": {
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/all-notes.db"
      }
    }
  }
}
```

### Alternative Configuration Methods

#### Using uvx (Recommended)

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "uvx",
      "args": ["mdquery"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/Notes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/notes.db"
      }
    }
  }
}
```

#### Direct Python Path

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "/path/to/python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Documents/Notes",
        "MDQUERY_DB_PATH": "/Users/username/.mdquery/notes.db"
      }
    }
  }
}
```

### Environment Variables

Configure mdquery behavior through environment variables:

**Essential Variables:**
- `MDQUERY_NOTES_DIR`: Directory containing markdown files to auto-index on startup
- `MDQUERY_DB_PATH`: Path to SQLite database file (default: `~/.mdquery/mdquery.db`)
- `MDQUERY_CACHE_DIR`: Directory for cache files (default: `~/.mdquery/cache`)

**Performance Variables:**
- `MDQUERY_PERFORMANCE_MODE`: Performance level (`low`, `medium`, `high`) - default: `medium`
- `MDQUERY_AUTO_OPTIMIZE`: Enable automatic query optimization (`true`/`false`) - default: `true`
- `MDQUERY_CONCURRENT_QUERIES`: Max concurrent queries (1-10) - default: `3`
- `MDQUERY_CACHE_TTL`: Cache time-to-live in minutes - default: `60`
- `MDQUERY_LAZY_LOADING`: Enable lazy loading for large datasets (`true`/`false`) - default: `true`

**Compatibility Variables:**
- `MDQUERY_ASSISTANT_TYPE`: Hint for response formatting (`claude`, `gpt`, `generic`) - auto-detected
- `MDQUERY_RESPONSE_FORMAT`: Default response format (`json`, `markdown`, `adaptive`) - default: `adaptive`

**Debug Variables:**
- `MDQUERY_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) - default: `INFO`
- `MDQUERY_MAX_RESULTS`: Default maximum results per query - default: `100`
- `MDQUERY_ENABLE_METRICS`: Enable performance metrics collection (`true`/`false`) - default: `false`

#### Configuration Approaches

**Approach 1: Single Notes Directory (Recommended for most users)**
- Set `MDQUERY_NOTES_DIR` to your main notes directory
- The server will automatically index this directory on startup
- Simple and straightforward

**Approach 2: Multiple Directories (Comma-separated)**
- Set `MDQUERY_NOTES_DIR` to comma-separated list of directories
- All directories are automatically indexed on startup
- Example: `MDQUERY_NOTES_DIR="/path/to/notes,/path/to/docs,/path/to/research"`

**Approach 3: Multiple Directories (Separate Servers)**
- Create separate MCP server entries for each directory
- Each gets its own database and can be queried independently
- Best for completely separate knowledge domains

**Approach 4: Manual Indexing Only**
- Don't set `MDQUERY_NOTES_DIR`
- Use `index_directory` tool to index directories as needed
- Full control over what gets indexed and when

## Basic Usage

### Initial Setup

Once configured, restart Claude Desktop and start a conversation:

#### Single Notes Directory (Auto-indexed)
If you configured `MDQUERY_NOTES_DIR`, your notes are automatically indexed on startup:

```
"I'd like to analyze my markdown notes. What patterns can you find?"
```

Claude will automatically:
1. Use the `get_schema` tool to understand your data structure
2. Use the `query_markdown` tool to analyze patterns

#### Multiple Notes Directories (Auto-indexed)
If you configured multiple directories with comma-separated `MDQUERY_NOTES_DIR`:

```
"I'd like to analyze my markdown notes across all my directories. What patterns can you find?"
```

Claude will automatically:
1. Use the `get_schema` tool to understand your data structure
2. Use the `query_markdown` tool to analyze patterns across all indexed directories

#### Multiple Separate Servers
If you configured separate MCP servers for different domains:

```
"I'd like to compare my personal notes with my work documentation. Can you analyze both?"
```

Claude will:
1. Query both servers independently
2. Compare patterns and themes across domains
3. Provide insights about knowledge overlap

#### Manual Indexing
For full control over indexing:

```
"I'd like to analyze my markdown notes. Can you help me index them and then find patterns?"
```

Claude will:
1. Use the `index_directory` tool to scan your notes
2. Use the `get_schema` tool to understand your data structure
3. Use the `query_markdown` tool to analyze patterns

### Common Requests

#### Content Discovery

```
"Find all my notes about machine learning from the last 6 months"

"Show me my most frequently used tags and how they've changed over time"

"What topics have I been writing about recently?"
```

#### Research Analysis

```
"Generate a research summary of my AI-related notes"

"Find similar content to my paper on neural networks"

"Extract all quotes and citations from my research notes"
```

#### Content Quality

```
"Analyze the SEO quality of my blog posts"

"Check the structure and readability of my documentation"

"Find files that might need updating based on their age and topic relevance"
```

#### Link Analysis

```
"Show me the relationship network between my notes"

"Find broken links in my documentation"

"Which notes are most connected to others?"
```

## Advanced Workflows

### Research Workflow

```
User: "I'm working on a literature review about transformer architectures. Can you help me organize my research?"

Claude will:
1. Index your notes directory
2. Find all transformer-related content
3. Analyze the structure and themes
4. Generate a research summary
5. Suggest gaps in your research
6. Create a bibliography from your citations
```

### Content Audit Workflow

```
User: "I need to audit my blog content for SEO and find opportunities for improvement"

Claude will:
1. Analyze SEO quality of all blog posts
2. Identify content structure issues
3. Find posts that need updating
4. Suggest internal linking opportunities
5. Generate a content improvement plan
```

### Knowledge Base Maintenance

```
User: "Help me maintain my personal knowledge base by finding outdated content and broken links"

Claude will:
1. Scan for broken internal and external links
2. Find content that hasn't been updated recently
3. Identify orphaned notes (no incoming links)
4. Suggest consolidation opportunities
5. Generate a maintenance checklist
```

## Available MCP Tools

### Core Query Tools

#### `query_markdown`
Execute SQL queries against your markdown database with automatic optimization.

**Features:**
- Automatic query optimization and performance enhancement
- Intelligent result caching for faster repeated queries
- Adaptive response formatting based on AI assistant type
- Support for concurrent queries from multiple assistants

**Example Usage:**
```
"Query my notes to find all files tagged with 'research' that were modified in the last month"
```

#### `comprehensive_tag_analysis`
**NEW**: Generate comprehensive analysis of tagged content with intelligent grouping.

**Features:**
- Semantic grouping of related tags and content
- Actionable insights and theoretical analysis
- Content quality filtering and optimization suggestions
- Performance-optimized for large tag datasets

**Example Usage:**
```
"Perform a comprehensive analysis of my AI and machine learning tags to find patterns and insights"
```

#### `get_schema`
Understand the structure of your notes database.

**Example Usage:**
```
"Show me the database schema so I understand what data is available"
```

### Indexing Tools

#### `index_directory`
Index markdown files in a single directory.

**Example Usage:**
```
"Index my notes directory at ~/Documents/Notes"
```

#### `index_multiple_directories`
Index markdown files in multiple directories at once (for manual indexing).

**Example Usage:**
```
"Index additional directories: ~/Temp/Notes, ~/Archive/OldNotes"
```

*Note: For regular use, configure multiple directories in your MCP server setup instead.*

### Performance and Monitoring Tools

#### `get_performance_stats`
**NEW**: Get real-time performance statistics and monitoring data.

**Features:**
- Query execution time analysis
- Cache hit rate monitoring
- Memory usage tracking
- Performance optimization suggestions

**Example Usage:**
```
"Show me the performance statistics for my mdquery server and suggest optimizations"
```

#### `optimize_query_performance`
**NEW**: Automatically optimize query performance and suggest improvements.

**Features:**
- Automatic query rewriting for better performance
- FTS (Full-Text Search) conversion for text searches
- Index usage optimization
- Performance impact analysis

**Example Usage:**
```
"Optimize the performance of my content search queries and show me the improvements"
```

#### `analyze_content_structure`
Analyze document structure and hierarchy.

**Example Usage:**
```
"Check the structure of my documentation files"
```

#### `find_similar_content`
Find content similar to a specific file.

**Example Usage:**
```
"Find notes similar to my machine learning paper"
```

### Research Tools

#### `fuzzy_search`
Perform fuzzy text matching for content discovery.

**Example Usage:**
```
"Find content related to 'neural network architectures' even if the exact phrase isn't used"
```

#### `generate_research_summary`
Generate comprehensive research summaries.

**Example Usage:**
```
"Generate a research summary for all my AI-related notes from 2024"
```

#### `extract_quotes_with_attribution`
Extract quotes and references with source attribution.

**Example Usage:**
```
"Extract all quotes from my research papers with proper attribution"
```

## Enhanced Features

### Automatic Error Recovery

mdquery now includes robust error recovery mechanisms that handle common issues automatically:

#### Database Issues
- **Corruption Recovery**: Automatic database rebuild when corruption is detected
- **Lock Resolution**: Intelligent retry with backoff for database lock conflicts
- **Permission Handling**: Clear guidance for permission-related issues
- **Disk Space Management**: Automatic cleanup of temporary files when disk space is low

#### Indexing Resilience
- **Corrupted File Handling**: Skip corrupted files and continue indexing
- **Network Drive Recovery**: Automatic retry for disconnected network drives
- **Incremental Fallback**: Fall back to incremental indexing when full indexing fails
- **Directory Validation**: Automatic creation of missing directories

**Example Recovery Scenarios:**
```
# Database corruption detected
🔧 "Database corruption detected and automatically repaired. Your data has been restored."

# Network drive disconnected
🔧 "Network connection restored. Indexing completed successfully."

# Corrupted file found
🔧 "Corrupted file detected and skipped. Indexing continued with remaining valid files."
```

### Multi-Assistant Compatibility

mdquery automatically adapts its responses for different AI assistants:

#### Supported Assistants
- **Claude (Anthropic)**: Detailed, verbose responses with rich formatting
- **ChatGPT (OpenAI)**: Structured, concise responses optimized for GPT models
- **Generic MCP Clients**: Standard JSON responses for universal compatibility
- **Custom Assistants**: Adaptive formatting based on client capabilities

#### Adaptive Response Formatting
- **Content Optimization**: Responses tailored to each assistant's strengths
- **Format Adaptation**: JSON, Markdown, or hybrid formats based on client preferences
- **Verbosity Control**: Detailed explanations for Claude, concise data for GPT
- **Error Message Clarity**: Assistant-specific error formatting and guidance

#### Concurrent Access
- **Multi-User Support**: Multiple assistants can query simultaneously
- **Request Prioritization**: Intelligent queuing and priority management
- **Resource Sharing**: Shared cache and optimization benefits across assistants
- **Isolation**: Each assistant maintains independent session context

**Usage Example:**
```json
// Claude Desktop configuration
{
  "mcpServers": {
    "mdquery-claude": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Notes",
        "MDQUERY_ASSISTANT_TYPE": "claude"
      }
    }
  }
}

// ChatGPT configuration (hypothetical)
{
  "mcpServers": {
    "mdquery-gpt": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_NOTES_DIR": "/Users/username/Notes",
        "MDQUERY_ASSISTANT_TYPE": "gpt"
      }
    }
  }
}
```

### Performance Optimizations

#### Query Optimization
- **Automatic FTS Conversion**: Text searches automatically use Full-Text Search indexes
- **Query Rewriting**: Complex queries optimized for better performance
- **Result Limiting**: Intelligent LIMIT clause addition for large result sets
- **Index Utilization**: Automatic selection of optimal database indexes

#### Caching System
- **Result Caching**: Frequently accessed results cached for instant retrieval
- **Analysis Caching**: Complex analysis results cached across sessions
- **Adaptive TTL**: Cache time-to-live adjusted based on content volatility
- **Memory Management**: Intelligent cache eviction and memory optimization

#### Lazy Loading
- **Component Loading**: Analysis components loaded only when needed
- **Progressive Indexing**: Large directories indexed incrementally
- **On-Demand Analysis**: Complex analysis performed only when requested
- **Resource Conservation**: Reduced memory footprint and startup time

**Performance Monitoring:**
```
"Show me performance statistics for my mdquery server"

📊 Response includes:
- Average query execution time: 0.75ms
- Cache hit rate: 85%
- Memory usage: 45MB
- Optimization suggestions: "Consider enabling FTS for content searches"
```

### Effective Prompting

#### Be Specific About Your Goals
```
❌ "Analyze my notes"
✅ "Analyze my research notes to find the most common themes and identify gaps in my literature review"
```

#### Provide Context
```
❌ "Find similar content"
✅ "Find content similar to my paper on transformer architectures, focusing on technical implementation details"
```

#### Ask for Actionable Insights
```
❌ "Show me statistics"
✅ "Show me content statistics and suggest which topics I should write more about"
```

### Organizing Your Notes for MCP

#### Use Consistent Tagging
```yaml
---
title: "Transformer Architecture Overview"
tags: [ai, machine-learning, transformers, research]
category: research
status: draft
---
```

#### Include Rich Frontmatter
```yaml
---
title: "Blog Post Title"
date: 2024-03-15
author: John Doe
tags: [blogging, seo, content]
seo_title: "Optimized Title for Search"
description: "Meta description for SEO"
word_count: 1250
---
```

#### Use Descriptive Filenames
```
research-transformer-attention-mechanisms.md
blog-2024-03-15-seo-optimization-guide.md
notes-meeting-2024-03-15-project-planning.md
```

### Performance Optimization

#### Regular Indexing
Set up regular indexing to keep your database current:

```
"Index my notes directory and show me what's new since last time"
```

#### Incremental Updates
Use incremental indexing for large note collections:

```
"Perform an incremental index of my notes to catch any changes"
```

#### Targeted Analysis
Focus analysis on specific subsets when working with large collections:

```
"Analyze only my research notes from the last 3 months"
```

## Troubleshooting

### Common Issues

#### MCP Server Won't Start

**Symptoms**: Claude can't connect to mdquery tools

**Solutions**:
1. Check Python installation: `python --version`
2. Verify mdquery installation: `python -c "import mdquery.mcp"`
3. Test server directly: `python -m mdquery.mcp_server`
4. Check file permissions on database path
5. Verify environment variables are set correctly

#### Database Connection Errors

**Symptoms**: "Database locked" or "Permission denied" errors

**Solutions**:
1. Ensure database directory exists and is writable
2. Close other applications that might be using the database
3. Check file permissions: `ls -la ~/.mdquery/`
4. Try a different database path

#### Auto-indexing Not Working

**Symptoms**: Notes directory not indexed automatically on startup

**Solutions**:
1. Verify `MDQUERY_NOTES_DIR` is set correctly
2. Check directory exists and is readable: `ls -la "$MDQUERY_NOTES_DIR"`
3. Check server logs for indexing errors
4. Manually index: "Index my notes directory at [path]"

#### Multiple Directories Not Indexing

**Symptoms**: Some directories missing from index when using multiple paths

**Solutions**:
1. Use `index_multiple_directories` tool with comma-separated paths
2. Verify all directory paths exist and are readable
3. Check for permission issues on individual directories
4. Index directories one at a time to isolate issues

#### Query Performance Issues

**Symptoms**: Slow responses or timeouts

**Solutions**:
1. Index your notes first: "Index my notes directory"
2. Use more specific queries instead of broad searches
3. Limit result sets: "Show me the top 10 most recent notes"
4. Check database size and consider cleanup

#### Incomplete Results

**Symptoms**: Missing files or data in results

**Solutions**:
1. Re-index your notes: "Re-index my entire notes directory"
2. Check file extensions are supported (.md, .markdown)
3. Verify file encoding (UTF-8 recommended)
4. Check for file permission issues

#### Environment Variables Not Working

**Symptoms**: Server ignores environment variable settings

**Solutions**:
1. Verify variables are exported: `echo $MDQUERY_NOTES_DIR`
2. Restart Claude Desktop after changing configuration
3. Use absolute paths instead of relative paths
4. Check for typos in variable names

### Debug Mode

Enable debug logging for troubleshooting:

```bash
MDQUERY_LOG_LEVEL=DEBUG python -m mdquery.mcp_server
```

### Getting Help

If you encounter issues:

1. Check the [troubleshooting section](../api/interfaces/mcp-server.md#troubleshooting) in the MCP API documentation
2. Review the [GitHub issues](https://github.com/your-org/mdquery/issues) for similar problems
3. Enable debug logging and check the output
4. Test the CLI interface to isolate MCP-specific issues

## Advanced Integration

### Custom AI Assistant Integration

If you're building your own AI assistant, you can integrate with mdquery's MCP server:

```python
import asyncio
from mdquery.mcp import MDQueryMCPServer

async def ai_assistant_query(user_query: str):
    server = MDQueryMCPServer()

    # Analyze user query and determine appropriate tools
    if "research" in user_query.lower():
        # Use research tools
        summary = await server.generate_research_summary()
        return json.loads(summary)
    elif "similar" in user_query.lower():
        # Use similarity search
        results = await server.fuzzy_search(user_query)
        return json.loads(results)
    else:
        # Use general query
        results = await server.query_markdown(f"SELECT * FROM files WHERE content MATCH '{user_query}'")
        return json.loads(results)
```

### Workflow Automation

Create automated workflows that combine multiple MCP tools:

```python
async def content_audit_workflow(server):
    # 1. Index latest content
    await server.index_directory("~/blog", incremental=True)

    # 2. Analyze SEO
    seo_results = await server.analyze_seo()

    # 3. Check for broken links
    link_analysis = await server.analyze_link_relationships()

    # 4. Generate comprehensive report
    report = await server.generate_content_report()

    return {
        'seo_analysis': json.loads(seo_results),
        'link_analysis': json.loads(link_analysis),
        'content_report': json.loads(report)
    }
```

## Examples and Use Cases

### Academic Research

```
"I'm working on a PhD thesis about natural language processing. Help me:
1. Index all my research notes
2. Find gaps in my literature review
3. Generate a bibliography from my citations
4. Identify the most important papers I've referenced
5. Suggest related topics I should explore"
```

### Content Marketing

```
"I manage a tech blog. Help me:
1. Analyze the SEO quality of all my posts
2. Find opportunities for internal linking
3. Identify content that needs updating
4. Suggest new topics based on my existing content
5. Generate a content calendar for next quarter"
```

### Personal Knowledge Management

```
"I maintain a personal knowledge base. Help me:
1. Find notes that haven't been updated in over a year
2. Identify orphaned notes with no connections
3. Suggest ways to better organize my content
4. Find duplicate or similar content that could be consolidated
5. Generate a map of my knowledge domains"
```

The MCP integration makes mdquery incredibly powerful by combining the precision of SQL queries with the intelligence of AI assistants, enabling sophisticated analysis and insights from your markdown content.