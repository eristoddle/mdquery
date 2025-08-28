# Tool Overview & Core Value

## Introduction

The mdquery tool is a universal markdown querying CLI tool that enables SQL-like search across diverse note-taking systems including Obsidian, Joplin, Jekyll, and generic markdown files. It provides a powerful interface for knowledge base querying, research analysis, and workflow automation through its sophisticated architecture combining indexing, parsing, and query execution capabilities.

At its core, mdquery transforms unstructured markdown content into a structured database that can be queried using familiar SQL syntax. This allows users to perform complex searches and analyses on their knowledge bases without needing to understand the underlying implementation details. The tool's value proposition centers on its ability to unify disparate markdown-based systems under a single query interface, making it easier to extract insights from personal knowledge repositories.

## Core Architecture

The mdquery system consists of four primary components that work together to enable powerful querying of markdown repositories: the indexer, database layer, query engine, and data models. These components follow a clear separation of concerns, with the indexer responsible for data ingestion, the database layer for storage and retrieval, the query engine for processing queries, and data models for representing structured information.

### Indexer Architecture

The indexer scans directories and processes files through a modular parser pipeline, extracting structured data from markdown files. This data is stored in a SQLite database with FTS5 virtual tables enabled for full-text search capabilities.

### Database Layer with SQLite FTS5

The database layer uses SQLite with FTS5 for embedded, high-performance full-text search. The schema is designed to store all extracted information from markdown files in a structured format, including:

- **files**: Core file metadata including path, modification date, and size
- **frontmatter**: Key-value pairs extracted from YAML/JSON/TOML frontmatter
- **tags**: Tags extracted from both frontmatter and content
- **links**: Links extracted from markdown content
- **content_fts**: FTS5 virtual table for full-text search across content
- **Obsidian-specific tables**: Additional tables for Obsidian features

### Query Engine

The query engine executes validated SQL-like queries against this schema, returning results in multiple formats. It includes comprehensive validation, security checks, and execution optimization.

### Data Models and Schema Representation

The system uses structured data models to represent markdown content and metadata, ensuring consistency and providing a clear interface for data access.

## Primary Use Cases

1. **Knowledge Base Search**: Find specific information across large collections of notes
2. **Content Analysis**: Analyze tag patterns, link structures, and content relationships
3. **Research Support**: Extract insights from research notes and documentation
4. **Workflow Automation**: Integrate with tools and scripts for automated processing

## Integration Ecosystem

The system supports both command-line interface (CLI) and MCP server deployment models, providing flexibility for different use cases:

- **CLI Interface**: Direct interaction for indexing and querying
- **MCP Server**: Programmatic access for AI assistant integration
- **Python API**: Programmatic access for custom applications

## Extensibility Model

The architecture emphasizes extensibility through:

- **Modular Parser Design**: Support for multiple markdown systems
- **Configuration System**: Flexible configuration options
- **Plugin Architecture**: Ability to add new parsers and features
- **API Access**: Both CLI and programmatic interfaces

## Performance and Reliability

The system includes features for performance optimization and reliability:

- **Incremental Indexing**: Efficient updates for large collections
- **Caching Layer**: Reduces I/O and parsing overhead
- **Error Handling**: Comprehensive error recovery mechanisms
- **Query Optimization**: Automatic query optimization for better performance

## Conclusion

mdquery provides a comprehensive solution for querying and analyzing markdown content across different systems, with a focus on performance, extensibility, and ease of use. Its modular architecture and powerful query capabilities make it an essential tool for anyone working with large collections of markdown files.