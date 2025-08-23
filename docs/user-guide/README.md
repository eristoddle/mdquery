# mdquery User Guide

Welcome to mdquery - the universal markdown querying tool that lets you search and analyze your notes using familiar SQL syntax.

## What is mdquery?

mdquery is a powerful tool that indexes your markdown files and provides SQL-like querying capabilities. Whether you use Obsidian, Joplin, Jekyll, or any other markdown-based system, mdquery gives you a unified way to search and analyze your content.

## Quick Start

### Installation

```bash
pip install mdquery
```

### Basic Usage

1. **Index your notes:**
   ```bash
   mdquery index /path/to/your/notes
   ```

2. **Query your notes:**
   ```bash
   mdquery query "SELECT * FROM files WHERE tags LIKE '%research%'"
   ```

3. **View the database schema:**
   ```bash
   mdquery schema
   ```

## Key Features

- **Universal Compatibility**: Works with Obsidian, Joplin, Jekyll, and generic markdown
- **SQL-Like Queries**: Use familiar SQL syntax to search your notes
- **Full-Text Search**: Powered by SQLite FTS5 for fast content search
- **Rich Metadata**: Extract and query frontmatter, tags, links, and content
- **Multiple Interfaces**: Command-line tool and MCP server for AI integration
- **High Performance**: Efficient indexing and caching for large collections

## What's Next?

- [Installation Guide](installation.md) - Detailed installation instructions
- [Query Syntax](query-syntax.md) - Complete guide to writing queries
- [Examples](examples/) - Real-world usage examples
- [Best Practices](best-practices.md) - Tips for effective use
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Use Cases

### For Researchers
- Find related notes across different topics
- Analyze research themes and patterns
- Track source citations and references
- Generate bibliographies from your notes

### For Content Creators
- Analyze blog post performance metrics
- Find content gaps and opportunities
- Track tag usage and categorization
- Optimize SEO metadata across posts

### For Knowledge Workers
- Search across multiple note-taking systems
- Find connections between ideas and projects
- Track project progress and status
- Generate reports from your notes

### For Developers
- Document code projects and decisions
- Track technical research and solutions
- Analyze documentation coverage
- Generate project reports and summaries

## Community and Support

- **Documentation**: Complete guides and API reference
- **Examples**: Real-world usage patterns and templates
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Share tips and ask questions in our community

Ready to get started? Head to the [Installation Guide](installation.md) to set up mdquery for your workflow.