# MCP Integration Guide

This guide covers how to use mdquery with AI assistants through the Model Context Protocol (MCP) server integration.

## What is MCP?

The Model Context Protocol (MCP) is a standard for connecting AI assistants to external tools and data sources. mdquery's MCP server allows AI assistants like Claude to directly query and analyze your markdown files.

## Benefits of MCP Integration

- **Natural Language Queries**: Ask questions in plain English instead of writing SQL
- **Intelligent Analysis**: AI can perform complex analysis and generate insights
- **Automated Workflows**: AI can chain multiple operations together
- **Context Awareness**: AI understands your note structure and relationships

## Setup and Configuration

### Prerequisites

- Python 3.8 or higher
- mdquery installed with MCP support
- MCP-compatible AI assistant (Claude Desktop, etc.)

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

```json
{
  "mcpServers": {
    "mdquery": {
      "command": "python",
      "args": ["-m", "mdquery.mcp_server"],
      "env": {
        "MDQUERY_DB_PATH": "/Users/username/notes/mdquery.db",
        "MDQUERY_CACHE_DIR": "/Users/username/notes/.cache"
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
        "MDQUERY_DB_PATH": "/Users/username/notes/mdquery.db"
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
        "MDQUERY_DB_PATH": "/Users/username/notes/mdquery.db"
      }
    }
  }
}
```

### Environment Variables

Configure mdquery behavior through environment variables:

- `MDQUERY_DB_PATH`: Path to your notes database
- `MDQUERY_CACHE_DIR`: Directory for cache files
- `MDQUERY_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `MDQUERY_MAX_RESULTS`: Default maximum results per query

## Basic Usage

### Initial Setup

Once configured, restart Claude Desktop and start a conversation:

```
"I'd like to analyze my markdown notes. Can you help me index them and then find patterns?"
```

Claude will automatically:
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
Execute SQL queries against your markdown database.

**Example Usage:**
```
"Query my notes to find all files tagged with 'research' that were modified in the last month"
```

#### `get_schema`
Understand the structure of your notes database.

**Example Usage:**
```
"Show me the database schema so I understand what data is available"
```

### Indexing Tools

#### `index_directory`
Index markdown files in a directory.

**Example Usage:**
```
"Index my notes directory at ~/Documents/Notes"
```

### Analysis Tools

#### `analyze_seo`
Perform SEO analysis on your content.

**Example Usage:**
```
"Analyze the SEO quality of my blog posts and suggest improvements"
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

## Best Practices

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