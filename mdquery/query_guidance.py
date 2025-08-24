"""
Query guidance and template system for mdquery MCP server.

This module provides query syntax documentation, templates for common analysis patterns,
optimization suggestions, and examples library for tag-based and workflow analysis queries.
Implements requirements 5.1, 5.2, 5.3, 5.4, 5.5 from the MCP workflow optimization spec.
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


@dataclass
class QueryParameter:
    """Parameter definition for query templates."""
    name: str
    type: str  # 'string', 'number', 'boolean', 'list'
    description: str
    default: Optional[Any] = None
    required: bool = True
    examples: Optional[List[str]] = None


@dataclass
class QueryTemplate:
    """Template for common query patterns."""
    name: str
    description: str
    category: str  # 'tag-analysis', 'workflow', 'content', 'research', 'performance'
    sql_template: str
    parameters: List[QueryParameter]
    example_usage: str
    complexity: str  # 'basic', 'intermediate', 'advanced'
    performance_notes: Optional[str] = None


@dataclass
class QueryOptimization:
    """Query optimization suggestion."""
    issue: str
    suggestion: str
    example_before: str
    example_after: str
    performance_impact: str  # 'low', 'medium', 'high'


@dataclass
class QueryGuidance:
    """Complete query guidance response."""
    suggested_queries: List[QueryTemplate]
    optimization_tips: List[str]
    common_patterns: List[str]
    syntax_reference: Dict[str, Any]
    examples: List[Dict[str, str]]


class QueryGuidanceEngine:
    """
    Engine for providing query syntax guidance and templates.

    Implements requirements:
    - 5.1: Query syntax documentation
    - 5.2: Common patterns for tag-based analysis
    - 5.3: Templates for multi-dimensional analysis
    - 5.4: Optimal query approaches for specific analysis types
    - 5.5: Query optimization suggestions
    """

    def __init__(self):
        """Initialize the query guidance engine with templates and examples."""
        self.templates = self._initialize_templates()
        self.optimizations = self._initialize_optimizations()
        self.syntax_reference = self._initialize_syntax_reference()
        self.common_patterns = self._initialize_common_patterns()

    def get_query_guidance(self, analysis_type: str, content_description: str = "") -> QueryGuidance:
        """
        Provide query syntax guidance and examples for specific analysis needs.

        Args:
            analysis_type: Type of analysis needed (e.g., "tag-analysis", "workflow-review")
            content_description: Description of the content to analyze

        Returns:
            QueryGuidance object with suggested queries, tips, and examples
        """
        # Filter templates by analysis type
        relevant_templates = [
            template for template in self.templates
            if analysis_type.lower() in template.category.lower() or
               analysis_type.lower() in template.name.lower() or
               analysis_type.lower() in template.description.lower()
        ]

        # If no specific matches, provide general templates
        if not relevant_templates:
            relevant_templates = [
                template for template in self.templates
                if template.complexity in ['basic', 'intermediate']
            ][:5]

        # Get optimization tips relevant to the analysis type
        optimization_tips = self._get_optimization_tips(analysis_type)

        # Get common patterns for this analysis type
        patterns = self._get_common_patterns(analysis_type)

        # Get examples
        examples = self._get_examples(analysis_type, content_description)

        return QueryGuidance(
            suggested_queries=relevant_templates,
            optimization_tips=optimization_tips,
            common_patterns=patterns,
            syntax_reference=self.syntax_reference,
            examples=examples
        )

    def get_query_templates(self, category: Optional[str] = None,
                          complexity: Optional[str] = None) -> List[QueryTemplate]:
        """
        Get query templates filtered by category and complexity.

        Args:
            category: Filter by category ('tag-analysis', 'workflow', etc.)
            complexity: Filter by complexity ('basic', 'intermediate', 'advanced')

        Returns:
            List of matching query templates
        """
        templates = self.templates

        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]

        if complexity:
            templates = [t for t in templates if t.complexity.lower() == complexity.lower()]

        return templates

    def get_optimization_suggestions(self, query: str) -> List[QueryOptimization]:
        """
        Analyze a query and provide optimization suggestions.

        Args:
            query: SQL query to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []
        query_lower = query.lower()

        # Check for common performance issues
        for optimization in self.optimizations:
            if self._query_matches_issue(query_lower, optimization.issue):
                suggestions.append(optimization)

        return suggestions

    def _initialize_templates(self) -> List[QueryTemplate]:
        """Initialize the library of query templates."""
        return [
            # Tag Analysis Templates
            QueryTemplate(
                name="Basic Tag Analysis",
                description="Find all files with specific tags and analyze tag distribution",
                category="tag-analysis",
                sql_template="""
                SELECT
                    f.filename,
                    f.directory,
                    f.word_count,
                    GROUP_CONCAT(DISTINCT t.tag) as tags,
                    f.modified_date
                FROM files f
                JOIN tags t ON f.id = t.file_id
                WHERE t.tag IN ({tag_list})
                GROUP BY f.id
                ORDER BY f.modified_date DESC
                LIMIT {limit};
                """,
                parameters=[
                    QueryParameter("tag_list", "list", "Comma-separated list of tags to search for",
                                 examples=["'research', 'project'", "'ai', 'llm', 'coding'"]),
                    QueryParameter("limit", "number", "Maximum number of results", default=50)
                ],
                example_usage="Find files tagged with AI development topics",
                complexity="basic"
            ),

            QueryTemplate(
                name="Hierarchical Tag Analysis",
                description="Analyze hierarchical tags (e.g., 'ai/llm/coding') and their relationships",
                category="tag-analysis",
                sql_template="""
                WITH tag_hierarchy AS (
                    SELECT
                        t.tag,
                        CASE
                            WHEN t.tag LIKE '%/%' THEN SUBSTR(t.tag, 1, INSTR(t.tag, '/') - 1)
                            ELSE t.tag
                        END as parent_tag,
                        COUNT(DISTINCT t.file_id) as file_count
                    FROM tags t
                    WHERE t.tag LIKE '{tag_pattern}'
                    GROUP BY t.tag
                )
                SELECT
                    parent_tag,
                    COUNT(*) as subtag_count,
                    SUM(file_count) as total_files,
                    GROUP_CONCAT(tag) as subtags
                FROM tag_hierarchy
                GROUP BY parent_tag
                ORDER BY total_files DESC;
                """,
                parameters=[
                    QueryParameter("tag_pattern", "string", "Tag pattern with wildcards",
                                 examples=["ai/%", "project/%", "research/%"])
                ],
                example_usage="Analyze AI-related tag hierarchy and subtag distribution",
                complexity="intermediate"
            ),

            QueryTemplate(
                name="Tag Co-occurrence Analysis",
                description="Find tags that frequently appear together in the same files",
                category="tag-analysis",
                sql_template="""
                SELECT
                    t1.tag as tag1,
                    t2.tag as tag2,
                    COUNT(*) as co_occurrence,
                    ROUND(COUNT(*) * 100.0 / (
                        SELECT COUNT(DISTINCT file_id) FROM tags WHERE tag = t1.tag
                    ), 2) as percentage
                FROM tags t1
                JOIN tags t2 ON t1.file_id = t2.file_id AND t1.tag < t2.tag
                WHERE (t1.tag LIKE '{pattern1}' OR t2.tag LIKE '{pattern2}')
                GROUP BY t1.tag, t2.tag
                HAVING co_occurrence >= {min_occurrence}
                ORDER BY co_occurrence DESC
                LIMIT {limit};
                """,
                parameters=[
                    QueryParameter("pattern1", "string", "First tag pattern", examples=["ai%", "project%"]),
                    QueryParameter("pattern2", "string", "Second tag pattern", examples=["coding%", "research%"]),
                    QueryParameter("min_occurrence", "number", "Minimum co-occurrence count", default=2),
                    QueryParameter("limit", "number", "Maximum results", default=20)
                ],
                example_usage="Find which AI tags commonly appear with coding tags",
                complexity="advanced"
            ),

            # Workflow Analysis Templates
            QueryTemplate(
                name="Development Workflow Analysis",
                description="Analyze development workflow patterns and identify improvement opportunities",
                category="workflow",
                sql_template="""
                WITH workflow_files AS (
                    SELECT
                        f.id,
                        f.filename,
                        f.directory,
                        f.modified_date,
                        f.word_count,
                        GROUP_CONCAT(DISTINCT t.tag) as tags,
                        COUNT(DISTINCT l.link_target) as link_count
                    FROM files f
                    LEFT JOIN tags t ON f.id = t.file_id
                    LEFT JOIN links l ON f.id = l.file_id
                    WHERE t.tag IN ({workflow_tags})
                    GROUP BY f.id
                ),
                workflow_stats AS (
                    SELECT
                        CASE
                            WHEN tags LIKE '%mcp%' THEN 'MCP Development'
                            WHEN tags LIKE '%agent%' THEN 'Agent Development'
                            WHEN tags LIKE '%automation%' THEN 'Automation'
                            WHEN tags LIKE '%coding%' THEN 'General Coding'
                            ELSE 'Other'
                        END as workflow_type,
                        COUNT(*) as file_count,
                        AVG(word_count) as avg_content_length,
                        AVG(link_count) as avg_links,
                        MAX(modified_date) as last_activity
                    FROM workflow_files
                    GROUP BY workflow_type
                )
                SELECT * FROM workflow_stats
                ORDER BY file_count DESC;
                """,
                parameters=[
                    QueryParameter("workflow_tags", "list", "Workflow-related tags",
                                 examples=["'mcp', 'agent', 'automation', 'coding'"])
                ],
                example_usage="Analyze AI development workflow patterns and activity levels",
                complexity="advanced"
            ),

            QueryTemplate(
                name="Content Quality Assessment",
                description="Assess content quality based on length, links, and structure",
                category="workflow",
                sql_template="""
                SELECT
                    f.filename,
                    f.word_count,
                    f.heading_count,
                    COUNT(DISTINCT l.link_target) as external_links,
                    COUNT(DISTINCT t.tag) as tag_count,
                    CASE
                        WHEN f.word_count > 1000 AND f.heading_count > 3 THEN 'High Quality'
                        WHEN f.word_count > 500 AND f.heading_count > 1 THEN 'Medium Quality'
                        WHEN f.word_count > 100 THEN 'Basic Quality'
                        ELSE 'Low Quality'
                    END as quality_assessment,
                    f.modified_date
                FROM files f
                LEFT JOIN links l ON f.id = l.file_id AND l.is_internal = 0
                LEFT JOIN tags t ON f.id = t.file_id
                WHERE f.filename LIKE '{file_pattern}'
                GROUP BY f.id
                ORDER BY f.word_count DESC
                LIMIT {limit};
                """,
                parameters=[
                    QueryParameter("file_pattern", "string", "File pattern to analyze",
                                 default="%.md", examples=["%.md", "%project%", "%research%"]),
                    QueryParameter("limit", "number", "Maximum results", default=50)
                ],
                example_usage="Assess quality of project documentation files",
                complexity="intermediate"
            ),

            # Content Analysis Templates
            QueryTemplate(
                name="Content Gap Analysis",
                description="Identify topics with outdated or missing content",
                category="content",
                sql_template="""
                WITH topic_activity AS (
                    SELECT
                        t.tag as topic,
                        COUNT(*) as total_files,
                        COUNT(CASE WHEN f.modified_date > date('now', '-{days} days') THEN 1 END) as recent_files,
                        MAX(f.modified_date) as last_update,
                        AVG(f.word_count) as avg_content_length
                    FROM tags t
                    JOIN files f ON t.file_id = f.id
                    WHERE t.tag LIKE '{topic_pattern}'
                    GROUP BY t.tag
                )
                SELECT
                    topic,
                    total_files,
                    recent_files,
                    last_update,
                    ROUND(avg_content_length, 0) as avg_words,
                    CASE
                        WHEN recent_files = 0 AND total_files > 3 THEN 'Needs Update'
                        WHEN total_files < 2 THEN 'Needs More Content'
                        ELSE 'Active'
                    END as status
                FROM topic_activity
                WHERE total_files >= {min_files}
                ORDER BY
                    CASE status
                        WHEN 'Needs Update' THEN 1
                        WHEN 'Needs More Content' THEN 2
                        ELSE 3
                    END,
                    total_files DESC;
                """,
                parameters=[
                    QueryParameter("topic_pattern", "string", "Topic pattern to analyze",
                                 examples=["ai%", "project%", "research%"]),
                    QueryParameter("days", "number", "Days to consider as 'recent'", default=30),
                    QueryParameter("min_files", "number", "Minimum files to include topic", default=2)
                ],
                example_usage="Find AI topics that need content updates or expansion",
                complexity="advanced"
            ),

            # Research Templates
            QueryTemplate(
                name="Source Attribution Analysis",
                description="Track sources and citations across research notes",
                category="research",
                sql_template="""
                SELECT
                    f.filename,
                    l.link_target as source_url,
                    l.link_text as citation_context,
                    COUNT(*) OVER (PARTITION BY l.link_target) as source_frequency,
                    f.modified_date,
                    GROUP_CONCAT(DISTINCT t.tag) as research_topics
                FROM files f
                JOIN links l ON f.id = l.file_id
                LEFT JOIN tags t ON f.id = t.file_id
                WHERE l.is_internal = 0
                    AND l.link_target LIKE 'http%'
                    AND (t.tag LIKE '{research_pattern}' OR f.filename LIKE '%research%')
                GROUP BY f.id, l.link_target
                ORDER BY source_frequency DESC, f.modified_date DESC
                LIMIT {limit};
                """,
                parameters=[
                    QueryParameter("research_pattern", "string", "Research tag pattern",
                                 examples=["research%", "study%", "paper%"]),
                    QueryParameter("limit", "number", "Maximum results", default=50)
                ],
                example_usage="Track most frequently cited sources in research notes",
                complexity="intermediate"
            ),

            # Performance Analysis Templates
            QueryTemplate(
                name="Large File Analysis",
                description="Identify large files that might need optimization or splitting",
                category="performance",
                sql_template="""
                SELECT
                    f.filename,
                    f.directory,
                    f.word_count,
                    f.heading_count,
                    f.file_size,
                    ROUND(f.word_count / NULLIF(f.heading_count, 0), 1) as words_per_section,
                    COUNT(DISTINCT t.tag) as tag_count,
                    f.modified_date,
                    CASE
                        WHEN f.word_count > 5000 THEN 'Consider Splitting'
                        WHEN f.word_count > 2000 THEN 'Monitor Size'
                        ELSE 'Appropriate Size'
                    END as size_recommendation
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                WHERE f.word_count > {min_words}
                GROUP BY f.id
                ORDER BY f.word_count DESC
                LIMIT {limit};
                """,
                parameters=[
                    QueryParameter("min_words", "number", "Minimum word count to include", default=1000),
                    QueryParameter("limit", "number", "Maximum results", default=25)
                ],
                example_usage="Find large files that might benefit from restructuring",
                complexity="basic"
            )
        ]

    def _initialize_optimizations(self) -> List[QueryOptimization]:
        """Initialize query optimization suggestions."""
        return [
            QueryOptimization(
                issue="Using LIKE for text search instead of FTS",
                suggestion="Use the content_fts table for full-text search instead of LIKE on content",
                example_before="SELECT * FROM files WHERE content LIKE '%python%'",
                example_after="""SELECT f.* FROM files f
JOIN content_fts fts ON f.id = fts.file_id
WHERE content_fts MATCH 'python'""",
                performance_impact="high"
            ),

            QueryOptimization(
                issue="Missing LIMIT clause on large result sets",
                suggestion="Add LIMIT clause to prevent returning too many results",
                example_before="SELECT * FROM files ORDER BY modified_date DESC",
                example_after="SELECT * FROM files ORDER BY modified_date DESC LIMIT 100",
                performance_impact="medium"
            ),

            QueryOptimization(
                issue="Inefficient tag filtering with OR conditions",
                suggestion="Use IN clause or JOIN with a values table for multiple tag filters",
                example_before="WHERE t.tag = 'ai' OR t.tag = 'llm' OR t.tag = 'coding'",
                example_after="WHERE t.tag IN ('ai', 'llm', 'coding')",
                performance_impact="low"
            ),

            QueryOptimization(
                issue="Unnecessary GROUP_CONCAT in WHERE clause",
                suggestion="Filter individual tags before grouping, not after concatenation",
                example_before="""SELECT f.*, GROUP_CONCAT(t.tag) as tags FROM files f
JOIN tags t ON f.id = t.file_id
GROUP BY f.id
HAVING tags LIKE '%ai%'""",
                example_after="""SELECT f.*, GROUP_CONCAT(t.tag) as tags FROM files f
JOIN tags t ON f.id = t.file_id
WHERE f.id IN (SELECT file_id FROM tags WHERE tag LIKE '%ai%')
GROUP BY f.id""",
                performance_impact="medium"
            ),

            QueryOptimization(
                issue="Cartesian product in JOINs",
                suggestion="Add proper JOIN conditions to avoid cartesian products",
                example_before="FROM files f, tags t WHERE f.filename LIKE '%.md'",
                example_after="FROM files f JOIN tags t ON f.id = t.file_id WHERE f.filename LIKE '%.md'",
                performance_impact="high"
            )
        ]

    def _initialize_syntax_reference(self) -> Dict[str, Any]:
        """Initialize syntax reference documentation."""
        return {
            "tables": {
                "files": {
                    "description": "File metadata and statistics",
                    "key_columns": ["id", "filename", "directory", "modified_date", "word_count"],
                    "common_filters": ["filename LIKE", "directory LIKE", "modified_date >", "word_count BETWEEN"]
                },
                "tags": {
                    "description": "Tags extracted from frontmatter and content",
                    "key_columns": ["file_id", "tag", "source"],
                    "common_filters": ["tag =", "tag LIKE", "source ="]
                },
                "frontmatter": {
                    "description": "YAML frontmatter key-value pairs",
                    "key_columns": ["file_id", "key", "value", "value_type"],
                    "common_filters": ["key =", "value LIKE", "value_type ="]
                },
                "links": {
                    "description": "Links found in markdown content",
                    "key_columns": ["file_id", "link_target", "link_type", "is_internal"],
                    "common_filters": ["is_internal =", "link_type =", "link_target LIKE"]
                },
                "content_fts": {
                    "description": "Full-text searchable content (use for text search)",
                    "key_columns": ["file_id", "title", "content", "headings"],
                    "common_usage": "WHERE content_fts MATCH 'search terms'"
                }
            },
            "operators": {
                "comparison": ["=", "!=", "<", ">", "<=", ">="],
                "pattern": ["LIKE", "NOT LIKE", "GLOB"],
                "membership": ["IN", "NOT IN"],
                "null": ["IS NULL", "IS NOT NULL"],
                "fts": ["MATCH (for content_fts table only)"]
            },
            "functions": {
                "aggregation": ["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP_CONCAT"],
                "string": ["SUBSTR", "LENGTH", "UPPER", "LOWER", "TRIM"],
                "date": ["date", "datetime", "strftime", "julianday"],
                "conditional": ["CASE WHEN", "COALESCE", "NULLIF"]
            },
            "fts_syntax": {
                "basic": "content_fts MATCH 'term'",
                "phrase": "content_fts MATCH '\"exact phrase\"'",
                "boolean": "content_fts MATCH 'term1 AND term2'",
                "exclude": "content_fts MATCH 'term1 NOT term2'",
                "prefix": "content_fts MATCH 'term*'",
                "column_specific": "fts.title MATCH 'term'"
            }
        }

    def _initialize_common_patterns(self) -> List[str]:
        """Initialize common query patterns."""
        return [
            "Find files with specific tags: JOIN files f WITH tags t ON f.id = t.file_id WHERE t.tag = 'your_tag'",
            "Full-text search: JOIN files f WITH content_fts fts ON f.id = fts.file_id WHERE content_fts MATCH 'search_terms'",
            "Recent files: WHERE modified_date > date('now', '-30 days')",
            "Files by directory: WHERE directory LIKE '%folder_name%'",
            "Tag co-occurrence: Self-join tags table on file_id with different tag conditions",
            "Content statistics: Use word_count, heading_count, and aggregation functions",
            "External links: WHERE is_internal = 0 in links table",
            "Frontmatter filtering: JOIN with frontmatter table on key-value pairs",
            "File size analysis: Use file_size and word_count for content analysis",
            "Date range queries: Use BETWEEN with date functions for temporal analysis"
        ]

    def _get_optimization_tips(self, analysis_type: str) -> List[str]:
        """Get optimization tips relevant to the analysis type."""
        base_tips = [
            "Use LIMIT to prevent large result sets",
            "Use content_fts table for text search instead of LIKE on content",
            "Add specific WHERE conditions before JOINs when possible",
            "Use IN clause instead of multiple OR conditions for tag filtering"
        ]

        type_specific_tips = {
            "tag-analysis": [
                "Index on tags.tag is automatically created for fast tag lookups",
                "Use EXISTS subqueries for complex tag combinations",
                "Consider tag hierarchy patterns (parent/child) for better organization"
            ],
            "workflow": [
                "Combine file metadata with tag analysis for workflow insights",
                "Use date functions to analyze temporal patterns",
                "Group by directory or tag patterns to identify workflow stages"
            ],
            "content": [
                "Use word_count and heading_count for content quality metrics",
                "Combine FTS search with metadata filtering for precise results",
                "Consider file_size for performance when processing large files"
            ],
            "research": [
                "Track external links for source attribution",
                "Use frontmatter for structured research metadata",
                "Combine tag analysis with link analysis for research networks"
            ]
        }

        return base_tips + type_specific_tips.get(analysis_type.lower(), [])

    def _get_common_patterns(self, analysis_type: str) -> List[str]:
        """Get common patterns for specific analysis types."""
        all_patterns = self.common_patterns

        type_specific_patterns = {
            "tag-analysis": [
                "Hierarchical tags: WHERE tag LIKE 'parent/%' for nested tag analysis",
                "Tag frequency: GROUP BY tag with COUNT(*) for popularity analysis",
                "Multi-tag files: Use multiple EXISTS subqueries for AND conditions"
            ],
            "workflow": [
                "Workflow stages: Use CASE statements to categorize files by workflow stage",
                "Activity analysis: Combine modified_date with tag patterns",
                "Progress tracking: Use date ranges with tag evolution analysis"
            ],
            "content": [
                "Quality metrics: Combine word_count, heading_count, and link_count",
                "Content gaps: Use LEFT JOINs to find missing content areas",
                "Duplicate detection: Use GROUP BY with HAVING COUNT(*) > 1"
            ]
        }

        return all_patterns + type_specific_patterns.get(analysis_type.lower(), [])

    def _get_examples(self, analysis_type: str, content_description: str) -> List[Dict[str, str]]:
        """Get relevant examples for the analysis type."""
        examples = [
            {
                "title": "Find AI Development Files",
                "description": "Get all files related to AI development with their tags",
                "query": """SELECT f.filename, f.word_count, GROUP_CONCAT(t.tag) as tags
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE t.tag IN ('ai', 'llm', 'mcp', 'agent')
GROUP BY f.id
ORDER BY f.modified_date DESC;"""
            },
            {
                "title": "Tag Popularity Analysis",
                "description": "Find the most popular tags in your collection",
                "query": """SELECT tag, COUNT(*) as file_count
FROM tags
GROUP BY tag
ORDER BY file_count DESC
LIMIT 20;"""
            },
            {
                "title": "Recent Activity by Topic",
                "description": "Show recent activity across different topics",
                "query": """SELECT
    SUBSTR(t.tag, 1, INSTR(t.tag || '/', '/') - 1) as topic,
    COUNT(*) as recent_files,
    MAX(f.modified_date) as last_activity
FROM files f
JOIN tags t ON f.id = t.file_id
WHERE f.modified_date > date('now', '-30 days')
GROUP BY topic
ORDER BY recent_files DESC;"""
            }
        ]

        # Add type-specific examples
        if "tag" in analysis_type.lower():
            examples.extend([
                {
                    "title": "Hierarchical Tag Analysis",
                    "description": "Analyze nested tag structures",
                    "query": """SELECT
    CASE WHEN tag LIKE '%/%'
         THEN SUBSTR(tag, 1, INSTR(tag, '/') - 1)
         ELSE tag
    END as parent_tag,
    COUNT(*) as subtag_count
FROM tags
WHERE tag LIKE '%/%'
GROUP BY parent_tag
ORDER BY subtag_count DESC;"""
                }
            ])

        if "workflow" in analysis_type.lower():
            examples.extend([
                {
                    "title": "Development Workflow Analysis",
                    "description": "Analyze development workflow patterns",
                    "query": """WITH workflow_files AS (
    SELECT f.*, GROUP_CONCAT(t.tag) as tags
    FROM files f
    JOIN tags t ON f.id = t.file_id
    WHERE t.tag IN ('mcp', 'agent', 'automation', 'coding')
    GROUP BY f.id
)
SELECT
    CASE
        WHEN tags LIKE '%mcp%' THEN 'MCP Development'
        WHEN tags LIKE '%agent%' THEN 'Agent Development'
        ELSE 'General Development'
    END as workflow_type,
    COUNT(*) as file_count,
    AVG(word_count) as avg_content
FROM workflow_files
GROUP BY workflow_type;"""
                }
            ])

        return examples

    def _query_matches_issue(self, query: str, issue: str) -> bool:
        """Check if a query matches a specific optimization issue."""
        issue_patterns = {
            "like for text search": r"content\s+like\s+['\"]%.*%['\"]",
            "missing limit": r"select.*from.*(?!.*limit)",
            "or conditions": r"tag\s*=.*\s+or\s+.*tag\s*=",
            "group_concat in where": r"having.*group_concat.*like",
            "cartesian product": r"from\s+\w+\s*,\s*\w+(?!\s+on)"
        }

        for pattern_key, pattern in issue_patterns.items():
            if pattern_key in issue.lower() and re.search(pattern, query, re.IGNORECASE):
                return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert the guidance engine to a dictionary for JSON serialization."""
        return {
            "templates": [asdict(template) for template in self.templates],
            "optimizations": [asdict(opt) for opt in self.optimizations],
            "syntax_reference": self.syntax_reference,
            "common_patterns": self.common_patterns
        }