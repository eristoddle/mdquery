# Requirements Document

## Introduction

This specification addresses optimizing mdquery's MCP server implementation to support streamlined AI development workflows. The focus is on simplifying configuration to require only a notes directory path, with optional database and cache locations, while ensuring the AI assistant can seamlessly execute complex analytical queries like comprehensive reports on tagged content without manual intervention.

## Requirements

### Requirement 1

**User Story:** As an AI development researcher, I want to configure mdquery MCP server with just my Obsidian vault path, so that I can quickly connect it to my AI assistant without complex setup.

#### Acceptance Criteria

1. WHEN configuring the MCP server THEN the system SHALL require only the notes directory path as mandatory configuration
2. WHEN database path is not specified THEN the system SHALL default to `{notes_dir}/.mdquery/mdquery.db`
3. WHEN cache directory is not specified THEN the system SHALL default to `{notes_dir}/.mdquery/cache`
4. WHEN the MCP server starts THEN the system SHALL automatically create necessary directories if they don't exist
5. WHEN the MCP server starts THEN the system SHALL automatically perform initial indexing of the notes directory

### Requirement 2

**User Story:** As an AI assistant user, I want to ask for comprehensive reports on tagged content in natural language, so that I can get detailed analysis without knowing query syntax.

#### Acceptance Criteria

1. WHEN I request a report on tagged content THEN the AI SHALL automatically understand tag syntax and execute appropriate queries
2. WHEN I ask for content grouping by topics THEN the AI SHALL analyze tags and content to identify logical groupings
3. WHEN I request actionable and theoretical items THEN the AI SHALL distinguish between practical recommendations and conceptual insights
4. WHEN I ask to "remove fluff" THEN the AI SHALL focus on substantive content and filter out superficial information
5. WHEN generating reports THEN the system SHALL provide structured output with clear topic categorization

### Requirement 3

**User Story:** As an AI development platform builder, I want the MCP server to provide comprehensive query capabilities for development workflow analysis, so that I can identify patterns and improvements in my AI development process.

#### Acceptance Criteria

1. WHEN analyzing development-related tags THEN the system SHALL support complex tag hierarchies (e.g., "llm/coding", "ai/agents")
2. WHEN generating topic groups THEN the system SHALL identify related concepts (e.g., MCPs, agents, automation tools)
3. WHEN analyzing development workflows THEN the system SHALL extract actionable insights about process improvements
4. WHEN processing large note collections THEN the system SHALL maintain performance under 5 seconds for typical queries
5. WHEN identifying improvement opportunities THEN the system SHALL categorize findings by implementation difficulty and impact

### Requirement 4

**User Story:** As a user setting up the MCP integration, I want clear error handling and automatic recovery, so that the system works reliably without manual intervention.

#### Acceptance Criteria

1. WHEN the notes directory doesn't exist THEN the system SHALL provide a clear error message with suggested resolution
2. WHEN indexing fails THEN the system SHALL retry with incremental indexing and report specific issues
3. WHEN database corruption occurs THEN the system SHALL automatically rebuild the index from source files
4. WHEN the AI assistant makes queries THEN the system SHALL provide helpful error messages that guide query refinement
5. WHEN configuration is invalid THEN the system SHALL provide specific guidance on correct configuration format

### Requirement 5

**User Story:** As an AI assistant, I want access to query syntax documentation and examples, so that I can help users formulate effective queries without them needing to learn SQL.

#### Acceptance Criteria

1. WHEN the MCP server starts THEN the system SHALL expose a tool to get query syntax documentation
2. WHEN providing query examples THEN the system SHALL include common patterns for tag-based analysis
3. WHEN helping with complex queries THEN the system SHALL provide templates for multi-dimensional analysis
4. WHEN users request specific analysis types THEN the system SHALL suggest optimal query approaches
5. WHEN query performance is poor THEN the system SHALL suggest query optimizations

### Requirement 6

**User Story:** As a developer using multiple AI tools, I want the MCP server to work seamlessly across different AI assistants, so that I can use the same setup with various tools.

#### Acceptance Criteria

1. WHEN connecting to different AI assistants THEN the system SHALL maintain consistent tool interfaces
2. WHEN handling concurrent requests THEN the system SHALL maintain data consistency and performance
3. WHEN different assistants have different capabilities THEN the system SHALL adapt response formats appropriately
4. WHEN assistants request different output formats THEN the system SHALL support JSON, markdown, and structured text
5. WHEN multiple assistants access simultaneously THEN the system SHALL handle concurrent database access safely

### Requirement 7

**User Story:** As a user with an existing Obsidian vault, I want the system to understand Obsidian-specific features, so that I can leverage my existing note structure and linking patterns.

#### Acceptance Criteria

1. WHEN processing Obsidian vaults THEN the system SHALL correctly parse wikilinks and backlinks
2. WHEN analyzing Obsidian tags THEN the system SHALL support both hashtag and frontmatter tag formats
3. WHEN processing Obsidian templates THEN the system SHALL handle template syntax without errors
4. WHEN analyzing note relationships THEN the system SHALL map Obsidian's graph structure
5. WHEN generating reports THEN the system SHALL leverage Obsidian's metadata for enhanced analysis