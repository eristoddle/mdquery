# Implementation Plan

- [x] 1. Set up project structure and core interfaces
  - Create Python package structure with proper __init__.py files
  - Define core data models and type hints for QueryResult, FileMetadata, and ParsedContent
  - Set up project dependencies in requirements.txt (sqlite3, python-frontmatter, click, markdown)
  - _Requirements: 2.1, 2.2_

- [x] 2. Implement SQLite database schema and initialization
  - Create database schema with files, frontmatter, tags, links, and FTS5 tables
  - Implement database connection management and initialization functions
  - Create database migration system for schema updates
  - Write unit tests for database schema creation and validation
  - _Requirements: 4.1, 4.5_

- [x] 3. Build frontmatter parser component
  - Implement frontmatter extraction using python-frontmatter library
  - Add type inference for frontmatter values (string, number, boolean, array, date)
  - Handle multiple frontmatter formats (YAML, JSON, TOML)
  - Write unit tests for frontmatter parsing with various formats and edge cases
  - _Requirements: 1.3, 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4. Build markdown content parser
  - Implement markdown parsing to extract content, headings, and word counts
  - Create content sanitization for FTS5 indexing
  - Extract heading hierarchy and structure information
  - Write unit tests for markdown parsing with various content structures
  - _Requirements: 1.4_

- [x] 5. Build tag extraction parser
  - Implement tag extraction from frontmatter arrays
  - Add inline hashtag detection and parsing (#tag, #parent/child)
  - Handle Obsidian-style nested tags and tag normalization
  - Write unit tests for tag extraction from multiple sources and formats
  - _Requirements: 1.5, 5.1_

- [x] 6. Build link extraction parser
  - Implement markdown link parsing ([text](url))
  - Add wikilink parsing ([[page]] and [[page|alias]])
  - Detect and categorize internal vs external links
  - Write unit tests for link extraction with various link formats
  - _Requirements: 1.6, 5.1_

- [x] 7. Implement file indexing engine
  - Create file scanner for recursive directory traversal
  - Implement file metadata extraction (path, size, dates, hash)
  - Integrate all parsers to process markdown files completely
  - Add file change detection using modification times and content hashing
  - Write unit tests for file indexing with various file types and structures
  - _Requirements: 4.2, 4.3, 5.1, 5.2, 5.3, 5.4_

- [x] 8. Build cache management system
  - Implement SQLite database persistence and cache validation
  - Add incremental indexing for modified files only
  - Create cache cleanup for deleted files and orphaned entries
  - Write unit tests for cache management and invalidation logic
  - _Requirements: 4.3, 4.4, 4.5_

- [x] 9. Implement SQL query engine
  - Create query validation and SQL injection protection
  - Implement query execution against SQLite with FTS5 support
  - Add result formatting and serialization (JSON, CSV, table formats)
  - Create unified views for easy querying across all metadata
  - Write unit tests for query execution and result formatting
  - _Requirements: 1.1, 1.2, 6.1, 6.2, 6.5_

- [x] 10. Build CLI application interface
  - Implement click-based command-line interface
  - Add commands for querying, indexing, and schema inspection
  - Implement multiple output formats (JSON, CSV, table, markdown)
  - Add proper error handling and user-friendly error messages
  - Write integration tests for CLI commands and workflows
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 11. Implement MCP server interface
  - Create MCP server using Model Context Protocol Python SDK
  - Expose query_markdown, get_schema, index_directory, and get_file_content tools
  - Implement proper MCP error handling and response formatting
  - Add concurrent request handling and thread safety
  - Write integration tests for MCP server functionality and protocol compliance
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 12. Add advanced querying features for content analysis
  - Implement SEO analysis queries for titles, descriptions, categories
  - Add content structure analysis (heading hierarchy, word counts)
  - Create relationship queries for tag similarity and link analysis
  - Add aggregation support (COUNT, GROUP BY, etc.) for reporting
  - Write unit tests for advanced query features and content analysis
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 13. Implement research and synthesis features
  - Add fuzzy text matching capabilities for related content discovery
  - Implement cross-collection querying for multiple note sources
  - Create source attribution preservation for quotes and references
  - Add date range and topic-based filtering for research organization
  - Write unit tests for research features and content synthesis
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 14. Add comprehensive error handling and logging
  - Implement robust error handling for file system operations
  - Add graceful handling of parsing errors and corrupted files
  - Create comprehensive logging system for debugging and monitoring
  - Add performance monitoring and query timeout protection
  - Write unit tests for error handling scenarios and edge cases
  - _Requirements: 2.4, 3.4, 4.1, 4.2_

- [ ] 15. Create comprehensive test suite and documentation
  - Build test collections for Obsidian, Joplin, Jekyll, and generic markdown
  - Implement performance tests with large file collections (1000+ files)
  - Create integration tests for end-to-end workflows
  - Add comprehensive API documentation and usage examples
  - Write user documentation with query syntax examples and best practices
  - _Requirements: 1.1, 2.5, 5.1, 5.2, 5.3, 5.4, 5.5_