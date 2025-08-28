# mdquery Wiki

This wiki provides comprehensive documentation for the mdquery project - a universal tool for querying and analyzing markdown files using SQL-like syntax.

## Table of Contents

### Getting Started
1. [Tool Overview & Core Value](01-tool-overview-and-core-value.md) - Introduction to mdquery's capabilities and architecture
2. [Installation Guide](02-installation-guide.md) - Step-by-step installation instructions
3. [Quick Start Guide](03-quick-start-guide.md) - Get up and running quickly with basic usage examples

### Reference Documentation
4. [Command Reference](04-command-reference.md) - Complete reference for all CLI commands
5. [Query Syntax Guide](05-query-syntax-guide.md) - Comprehensive guide to SQL-like query syntax
6. [Configuration](06-configuration.md) - Configuration options and environment variables
7. [Supported Markdown Systems](07-supported-markdown-systems.md) - Support for Obsidian, Joplin, Jekyll, and generic markdown

### API and Integration
8. [Python API Reference](08-python-api-reference.md) - Programmatic access to mdquery functionality
9. [Performance Optimization](09-performance-optimization.md) - Caching, indexing strategies, and performance tuning
10. [AI Assistant Integration (MCP)](10-ai-assistant-integration-mcp.md) - Integration with AI assistants via Model Context Protocol

### Technical Documentation
11. [Database Schema Design](11-database-schema-design.md) - Database structure and relationships
12. [Error Handling and Troubleshooting](12-error-handling-and-troubleshooting.md) - Common issues and solutions
13. [Development Guide](13-development-guide.md) - Testing strategy, contribution guidelines, and development workflow

## Key Features

- **SQL-Like Querying**: Execute SELECT, JOIN, GROUP BY, and LIKE operations on markdown metadata and content
- **Multiple Format Support**: Works with Obsidian, Joplin, Jekyll, and generic markdown files
- **Full-Text Search**: Powered by SQLite FTS5 for fast content search
- **AI Integration**: MCP server support for integration with AI tools like Claude Desktop
- **Performance Optimized**: Caching, incremental indexing, and query optimization
- **Extensible Architecture**: Modular design supports custom parsers and configurations

## Quick Navigation

### For New Users
- Start with [Tool Overview](01-tool-overview-and-core-value.md) to understand mdquery's value proposition
- Follow the [Installation Guide](02-installation-guide.md) to set up mdquery
- Use the [Quick Start Guide](03-quick-start-guide.md) for your first queries

### For Power Users
- Explore [Advanced Query Features](05-query-syntax-guide.md#advanced-query-features) for complex analyses
- Configure [Performance Optimization](09-performance-optimization.md) for large repositories
- Set up [AI Assistant Integration](10-ai-assistant-integration-mcp.md) for enhanced workflows

### For Developers
- Review the [Python API Reference](08-python-api-reference.md) for programmatic access
- Check the [Development Guide](13-development-guide.md) for contribution guidelines
- Understand the [Database Schema](11-database-schema-design.md) for custom integrations

### For Troubleshooting
- Consult [Error Handling and Troubleshooting](12-error-handling-and-troubleshooting.md) for common issues
- Review [Configuration](06-configuration.md) for setup problems
- Check [Performance Optimization](09-performance-optimization.md) for performance issues

## System Requirements

- Python 3.8+
- SQLite3 (included with Python)
- 50MB+ available disk space
- Support for all major operating systems (Windows, macOS, Linux)

## Architecture Overview

mdquery follows a modular architecture with these core components:

- **Indexer**: Scans and processes markdown files
- **Database Layer**: SQLite with FTS5 for storage and search
- **Query Engine**: Executes and validates SQL-like queries
- **Parser Pipeline**: Extensible parsers for different markdown formats
- **CLI & MCP Server**: Multiple interfaces for different use cases

## Support and Community

- **Documentation**: This wiki provides comprehensive documentation
- **Issues**: Report bugs and request features via GitHub issues
- **Development**: Contribute following the [Development Guide](13-development-guide.md)
- **Performance**: Benchmark data shows support for 1000+ file repositories

## License

mdquery is released under the MIT License. See the main repository for full license details.

---

*This wiki is automatically generated from the project's knowledge base and is kept up-to-date with the latest features and best practices.*