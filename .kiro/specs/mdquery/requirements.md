# Requirements Document

## Introduction

mdquery is a universal markdown querying tool that provides SQL-like functionality for searching and analyzing markdown files across different note-taking systems and static site generators. The tool addresses the fragmentation in markdown tooling by offering a unified interface to query file metadata, frontmatter, content, tags, and links regardless of the source system (Obsidian, Joplin, Jekyll, etc.).

## Requirements

### Requirement 1

**User Story:** As a researcher, I want to query markdown files using SQL-like syntax, so that I can efficiently search across my notes from different tools without learning proprietary query languages.

#### Acceptance Criteria

1. WHEN a user provides a query string THEN the system SHALL parse it using SQL-like syntax
2. WHEN querying file metadata THEN the system SHALL support fields like directory, filename, modified_date, created_date, and file_size
3. WHEN querying frontmatter THEN the system SHALL extract and index YAML frontmatter fields as queryable columns
4. WHEN querying content THEN the system SHALL support full-text search across markdown body content
5. WHEN querying tags THEN the system SHALL extract and index both frontmatter tags and inline tags (e.g., #tag)
6. WHEN querying links THEN the system SHALL extract and index both markdown links and wikilinks

### Requirement 2

**User Story:** As a developer, I want a command-line Python application, so that I can integrate markdown querying into scripts and automation workflows.

#### Acceptance Criteria

1. WHEN the CLI is invoked with a query THEN the system SHALL execute the query and return results
2. WHEN the CLI is invoked with a directory path THEN the system SHALL recursively scan for markdown files
3. WHEN the CLI outputs results THEN the system SHALL support multiple output formats (JSON, CSV, table)
4. WHEN the CLI encounters errors THEN the system SHALL provide clear error messages and exit codes
5. WHEN the CLI is run with --help THEN the system SHALL display usage information and query syntax examples

### Requirement 3

**User Story:** As an AI assistant user, I want an MCP server for mdquery, so that I can query my markdown notes through AI conversations.

#### Acceptance Criteria

1. WHEN the MCP server receives a query request THEN the system SHALL execute the query and return structured results
2. WHEN the MCP server is initialized THEN the system SHALL expose query and schema inspection tools
3. WHEN the MCP server handles multiple concurrent requests THEN the system SHALL maintain performance and data consistency
4. WHEN the MCP server encounters errors THEN the system SHALL return proper MCP error responses

### Requirement 4

**User Story:** As a content creator, I want efficient querying performance, so that I can work with large collections of markdown files without delays.

#### Acceptance Criteria

1. WHEN processing large directories THEN the system SHALL complete indexing within reasonable time limits
2. WHEN executing queries THEN the system SHALL return results in under 1 second for typical collections
3. WHEN files are modified THEN the system SHALL support incremental re-indexing
4. WHEN using cached data THEN the system SHALL validate cache freshness against file modification times
5. IF using SQLite caching THEN the system SHALL persist indexes between sessions

### Requirement 5

**User Story:** As a multi-tool user, I want compatibility with different markdown formats, so that I can query notes from Obsidian, Joplin, Jekyll, and other systems uniformly.

#### Acceptance Criteria

1. WHEN processing Obsidian files THEN the system SHALL handle wikilinks, tags, and Obsidian-specific frontmatter
2. WHEN processing Joplin files THEN the system SHALL handle Joplin's markdown format and metadata
3. WHEN processing Jekyll files THEN the system SHALL handle Jekyll frontmatter and liquid tags
4. WHEN processing generic markdown THEN the system SHALL handle standard markdown syntax
5. WHEN encountering unknown frontmatter fields THEN the system SHALL include them as queryable columns

### Requirement 6

**User Story:** As a blog maintainer, I want to analyze and optimize my content, so that I can improve SEO and content organization.

#### Acceptance Criteria

1. WHEN querying for SEO analysis THEN the system SHALL support queries on title, description, categories, and tags
2. WHEN analyzing content structure THEN the system SHALL extract heading hierarchy and word counts
3. WHEN finding related content THEN the system SHALL support queries based on tag similarity and link relationships
4. WHEN identifying content gaps THEN the system SHALL support queries for missing categories or underused tags
5. WHEN generating reports THEN the system SHALL support aggregation queries (COUNT, GROUP BY, etc.)

### Requirement 7

**User Story:** As a researcher, I want to compile insights from web clips and notes, so that I can efficiently synthesize information for articles and summaries.

#### Acceptance Criteria

1. WHEN searching across multiple sources THEN the system SHALL support queries spanning different note collections
2. WHEN finding related notes THEN the system SHALL support fuzzy text matching and semantic similarity
3. WHEN extracting quotes THEN the system SHALL preserve source attribution and context
4. WHEN organizing research THEN the system SHALL support queries by research topic, source, and date ranges
5. WHEN exporting findings THEN the system SHALL support result formatting for further processing