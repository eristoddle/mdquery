"""
Advanced querying features for content analysis.

This module provides specialized query functions for SEO analysis, content structure
analysis, relationship queries, and reporting aggregations. It extends the base
QueryEngine with domain-specific query builders and analysis functions.
"""

import sqlite3
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re
import math

from .models import QueryResult
from .query import QueryEngine, QueryError

logger = logging.getLogger(__name__)


@dataclass
class SEOAnalysis:
    """Results of SEO analysis for markdown files."""
    file_path: str
    title: Optional[str]
    description: Optional[str]
    category: Optional[str]
    word_count: int
    heading_count: int
    tags: List[str]
    issues: List[str]
    score: float


@dataclass
class ContentStructure:
    """Analysis of content structure and hierarchy."""
    file_path: str
    heading_hierarchy: List[Dict[str, Any]]
    word_count: int
    paragraph_count: int
    readability_score: Optional[float]
    structure_issues: List[str]


@dataclass
class TagSimilarity:
    """Tag similarity analysis between files."""
    file1_path: str
    file2_path: str
    common_tags: List[str]
    similarity_score: float
    total_tags_file1: int
    total_tags_file2: int


@dataclass
class LinkAnalysis:
    """Link relationship analysis."""
    source_file: str
    target_file: str
    link_type: str
    is_bidirectional: bool
    link_strength: float


class AdvancedQueryEngine:
    """
    Advanced query engine for content analysis and reporting.

    Provides specialized methods for SEO analysis, content structure analysis,
    relationship queries, and aggregation reporting on top of the base QueryEngine.
    """

    def __init__(self, query_engine: QueryEngine):
        """
        Initialize advanced query engine.

        Args:
            query_engine: Base query engine instance
        """
        self.query_engine = query_engine
        self.db_manager = query_engine.db_manager

    def analyze_seo(self, file_paths: Optional[List[str]] = None) -> List[SEOAnalysis]:
        """
        Perform SEO analysis on markdown files.

        Analyzes titles, descriptions, categories, word counts, and identifies
        common SEO issues like missing metadata or poor content structure.

        Args:
            file_paths: Optional list of specific file paths to analyze.
                       If None, analyzes all files.

        Returns:
            List of SEO analysis results
        """
        # Build query to get files with metadata
        base_query = """
            SELECT
                f.path,
                f.word_count,
                f.heading_count,
                fm_title.value as title,
                fm_description.value as description,
                fm_category.value as category,
                GROUP_CONCAT(t.tag) as tags
            FROM files f
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_description ON f.id = fm_description.file_id AND fm_description.key = 'description'
            LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
            LEFT JOIN tags t ON f.id = t.file_id
        """

        if file_paths is not None:
            if len(file_paths) == 0:
                # Return empty list for empty file paths
                return []
            placeholders = ','.join('?' * len(file_paths))
            query = f"{base_query} WHERE f.path IN ({placeholders}) GROUP BY f.id"
            result = self.query_engine.execute_query(query, file_paths)
        else:
            query = f"{base_query} GROUP BY f.id"
            result = self.query_engine.execute_query(query)

        analyses = []
        for row in result.rows:
            analysis = self._analyze_seo_for_file(row)
            analyses.append(analysis)

        return analyses

    def _analyze_seo_for_file(self, file_data: Dict[str, Any]) -> SEOAnalysis:
        """Analyze SEO for a single file."""
        issues = []
        score = 100.0  # Start with perfect score and deduct points

        # Check title
        title = file_data.get('title')
        if not title:
            issues.append("Missing title in frontmatter")
            score -= 20
        elif len(title) < 10:
            issues.append("Title too short (< 10 characters)")
            score -= 10
        elif len(title) > 60:
            issues.append("Title too long (> 60 characters)")
            score -= 10

        # Check description
        description = file_data.get('description')
        if not description:
            issues.append("Missing description in frontmatter")
            score -= 15
        elif len(description) < 50:
            issues.append("Description too short (< 50 characters)")
            score -= 10
        elif len(description) > 160:
            issues.append("Description too long (> 160 characters)")
            score -= 10

        # Check category
        category = file_data.get('category')
        if not category:
            issues.append("Missing category classification")
            score -= 10

        # Check word count
        word_count = file_data.get('word_count', 0)
        if word_count < 300:
            issues.append("Content too short (< 300 words)")
            score -= 15
        elif word_count > 3000:
            issues.append("Content very long (> 3000 words) - consider breaking up")
            score -= 5

        # Check heading structure
        heading_count = file_data.get('heading_count', 0)
        if heading_count == 0:
            issues.append("No headings found - poor content structure")
            score -= 15
        elif word_count > 500 and heading_count < 2:
            issues.append("Long content with few headings - poor readability")
            score -= 10

        # Check tags
        tags_str = file_data.get('tags', '')
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
        if not tags:
            issues.append("No tags found - poor discoverability")
            score -= 10
        elif len(tags) > 10:
            issues.append("Too many tags (> 10) - may dilute focus")
            score -= 5

        return SEOAnalysis(
            file_path=file_data['path'],
            title=title,
            description=description,
            category=category,
            word_count=word_count,
            heading_count=heading_count,
            tags=tags,
            issues=issues,
            score=max(0, score)  # Don't go below 0
        )

    def analyze_content_structure(self, file_paths: Optional[List[str]] = None) -> List[ContentStructure]:
        """
        Analyze content structure and hierarchy.

        Examines heading hierarchy, content organization, and readability
        to identify structural issues and improvement opportunities.

        Args:
            file_paths: Optional list of specific file paths to analyze

        Returns:
            List of content structure analyses
        """
        # Get files with content for analysis
        base_query = """
            SELECT
                f.path,
                f.word_count,
                f.heading_count,
                c.content,
                c.headings
            FROM files f
            JOIN content_fts c ON f.id = c.file_id
        """

        if file_paths:
            placeholders = ','.join('?' * len(file_paths))
            query = f"{base_query} WHERE f.path IN ({placeholders})"
            result = self.query_engine.execute_query(query, file_paths)
        else:
            query = base_query
            result = self.query_engine.execute_query(query)

        analyses = []
        for row in result.rows:
            analysis = self._analyze_content_structure_for_file(row)
            analyses.append(analysis)

        return analyses

    def _analyze_content_structure_for_file(self, file_data: Dict[str, Any]) -> ContentStructure:
        """Analyze content structure for a single file."""
        content = file_data.get('content', '')
        headings_str = file_data.get('headings', '')

        # Parse heading hierarchy
        heading_hierarchy = self._parse_heading_hierarchy(headings_str)

        # Count paragraphs (rough estimate)
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])

        # Calculate readability score (simplified)
        readability_score = self._calculate_readability_score(content)

        # Identify structure issues
        structure_issues = self._identify_structure_issues(
            heading_hierarchy,
            file_data.get('word_count', 0),
            paragraph_count
        )

        return ContentStructure(
            file_path=file_data['path'],
            heading_hierarchy=heading_hierarchy,
            word_count=file_data.get('word_count', 0),
            paragraph_count=paragraph_count,
            readability_score=readability_score,
            structure_issues=structure_issues
        )

    def _parse_heading_hierarchy(self, headings_str: str) -> List[Dict[str, Any]]:
        """Parse heading hierarchy from headings string."""
        if not headings_str:
            return []

        headings = []
        for heading in headings_str.split('\n'):
            heading = heading.strip()
            if heading:
                # Extract heading level and text
                level_match = re.match(r'^(#{1,6})\s*(.+)', heading)
                if level_match:
                    level = len(level_match.group(1))
                    text = level_match.group(2).strip()
                    headings.append({
                        'level': level,
                        'text': text,
                        'word_count': len(text.split())
                    })

        return headings

    def _calculate_readability_score(self, content: str) -> Optional[float]:
        """Calculate simplified readability score."""
        if not content:
            return None

        # Count sentences (rough estimate)
        sentences = len(re.findall(r'[.!?]+', content))
        if sentences == 0:
            return None

        # Count words
        words = len(content.split())
        if words == 0:
            return None

        # Count syllables (very rough estimate)
        syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', word))) for word in content.split())

        # Simplified Flesch Reading Ease formula
        if sentences > 0 and words > 0:
            avg_sentence_length = words / sentences
            avg_syllables_per_word = syllables / words
            score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
            return max(0, min(100, score))  # Clamp between 0-100

        return None

    def _identify_structure_issues(self, headings: List[Dict[str, Any]],
                                 word_count: int, paragraph_count: int) -> List[str]:
        """Identify content structure issues."""
        issues = []

        if not headings:
            if word_count > 200:
                issues.append("No headings in content longer than 200 words")
            # Don't return early - continue to check other issues

        # Check heading level progression (only if we have headings)
        if headings:
            prev_level = 0
            for heading in headings:
                level = heading['level']
                if level > prev_level + 1:
                    issues.append(f"Heading level jumps from H{prev_level} to H{level}")
                prev_level = level

            # Check for very long sections
            if word_count > 1000 and len(headings) < 3:
                issues.append("Long content with few headings - consider more structure")

        # Check paragraph density
        if paragraph_count > 0:
            words_per_paragraph = word_count / paragraph_count
            if words_per_paragraph > 150:
                issues.append("Very long paragraphs - consider breaking up")

        return issues

    def find_similar_content(self, file_path: str, similarity_threshold: float = 0.3) -> List[TagSimilarity]:
        """
        Find content similar to the given file based on tag overlap.

        Args:
            file_path: Path of the file to find similar content for
            similarity_threshold: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of similar files with similarity scores
        """
        # Get tags for the target file
        target_query = """
            SELECT t.tag
            FROM files f
            JOIN tags t ON f.id = t.file_id
            WHERE f.path = ?
        """
        target_result = self.query_engine.execute_query(target_query, [file_path])
        target_tags = set(row['tag'] for row in target_result.rows)

        if not target_tags:
            return []

        # Get all other files with their tags
        all_files_query = """
            SELECT
                f.path,
                GROUP_CONCAT(t.tag) as tags
            FROM files f
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE f.path != ?
            GROUP BY f.id, f.path
        """
        all_files_result = self.query_engine.execute_query(all_files_query, [file_path])

        similarities = []
        for row in all_files_result.rows:
            other_path = row['path']
            other_tags_str = row['tags'] or ''
            other_tags = set(tag.strip() for tag in other_tags_str.split(',') if tag.strip())

            if other_tags:
                similarity = self._calculate_tag_similarity(target_tags, other_tags)
                if similarity >= similarity_threshold:
                    common_tags = list(target_tags.intersection(other_tags))
                    similarities.append(TagSimilarity(
                        file1_path=file_path,
                        file2_path=other_path,
                        common_tags=common_tags,
                        similarity_score=similarity,
                        total_tags_file1=len(target_tags),
                        total_tags_file2=len(other_tags)
                    ))

        # Sort by similarity score descending
        similarities.sort(key=lambda x: x.similarity_score, reverse=True)
        return similarities

    def _calculate_tag_similarity(self, tags1: Set[str], tags2: Set[str]) -> float:
        """Calculate Jaccard similarity between two tag sets."""
        if not tags1 and not tags2:
            return 1.0
        if not tags1 or not tags2:
            return 0.0

        intersection = len(tags1.intersection(tags2))
        union = len(tags1.union(tags2))
        return intersection / union if union > 0 else 0.0

    def analyze_link_relationships(self) -> List[LinkAnalysis]:
        """
        Analyze link relationships between files.

        Identifies bidirectional links, link strength, and relationship patterns
        to understand content connectivity and navigation structure.

        Returns:
            List of link relationship analyses
        """
        # Get all internal links
        query = """
            SELECT
                f1.path as source_file,
                l.link_target,
                l.link_type,
                f2.path as target_file
            FROM files f1
            JOIN links l ON f1.id = l.file_id
            LEFT JOIN files f2 ON l.link_target = f2.path
            WHERE l.is_internal = 1
            ORDER BY f1.path, l.link_target
        """
        result = self.query_engine.execute_query(query)

        # Build link graph
        link_graph = defaultdict(list)
        all_links = []

        for row in result.rows:
            source = row['source_file']
            target = row['target_file'] or row['link_target']  # Use target_file if exists, else link_target
            link_type = row['link_type']

            link_graph[source].append(target)
            all_links.append((source, target, link_type))

        # Analyze relationships
        analyses = []
        processed_pairs = set()

        for source, target, link_type in all_links:
            if target and (source, target) not in processed_pairs:
                # Check if bidirectional
                is_bidirectional = target in link_graph and source in link_graph[target]

                # Calculate link strength (simple metric based on frequency and bidirectionality)
                forward_count = link_graph[source].count(target)
                backward_count = link_graph[target].count(source) if target in link_graph else 0
                link_strength = forward_count + (backward_count * 0.5) + (1.0 if is_bidirectional else 0.0)

                analyses.append(LinkAnalysis(
                    source_file=source,
                    target_file=target,
                    link_type=link_type,
                    is_bidirectional=is_bidirectional,
                    link_strength=link_strength
                ))

                processed_pairs.add((source, target))
                if is_bidirectional:
                    processed_pairs.add((target, source))

        # Sort by link strength descending
        analyses.sort(key=lambda x: x.link_strength, reverse=True)
        return analyses

    def generate_content_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive content analysis report.

        Provides aggregated statistics and insights about the entire
        markdown collection including SEO, structure, and relationship metrics.

        Returns:
            Dictionary containing comprehensive report data
        """
        report = {}

        # Basic statistics
        stats_query = """
            SELECT
                COUNT(*) as total_files,
                AVG(word_count) as avg_word_count,
                MAX(word_count) as max_word_count,
                MIN(word_count) as min_word_count,
                SUM(word_count) as total_words,
                AVG(heading_count) as avg_headings,
                COUNT(CASE WHEN word_count = 0 THEN 1 END) as empty_files
            FROM files
        """
        stats_result = self.query_engine.execute_query(stats_query)
        report['basic_stats'] = stats_result.rows[0] if stats_result.rows else {}

        # Frontmatter coverage
        frontmatter_query = """
            SELECT
                key,
                COUNT(*) as file_count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM files) as coverage_percent
            FROM frontmatter
            GROUP BY key
            ORDER BY file_count DESC
        """
        frontmatter_result = self.query_engine.execute_query(frontmatter_query)
        report['frontmatter_coverage'] = frontmatter_result.rows

        # Tag statistics
        tag_stats_query = """
            WITH tag_counts AS (
                SELECT file_id, COUNT(*) as tag_count
                FROM tags
                GROUP BY file_id
            )
            SELECT
                (SELECT COUNT(DISTINCT tag) FROM tags) as unique_tags,
                (SELECT COUNT(*) FROM tags) as total_tag_instances,
                AVG(tag_count) as avg_tags_per_file,
                MAX(tag_count) as max_tags_per_file
            FROM tag_counts
        """
        tag_stats_result = self.query_engine.execute_query(tag_stats_query)
        report['tag_stats'] = tag_stats_result.rows[0] if tag_stats_result.rows else {}

        # Most popular tags
        popular_tags_query = """
            SELECT tag, COUNT(*) as usage_count
            FROM tags
            GROUP BY tag
            ORDER BY usage_count DESC
            LIMIT 20
        """
        popular_tags_result = self.query_engine.execute_query(popular_tags_query)
        report['popular_tags'] = popular_tags_result.rows

        # Link statistics
        link_stats_query = """
            SELECT
                COUNT(*) as total_links,
                COUNT(CASE WHEN is_internal = 1 THEN 1 END) as internal_links,
                COUNT(CASE WHEN is_internal = 0 THEN 1 END) as external_links,
                COUNT(DISTINCT link_target) as unique_targets,
                link_type,
                COUNT(*) as type_count
            FROM links
            GROUP BY link_type
        """
        link_stats_result = self.query_engine.execute_query(link_stats_query)
        report['link_stats'] = link_stats_result.rows

        # Files without metadata
        missing_metadata_query = """
            SELECT
                f.path,
                CASE WHEN fm_title.value IS NULL THEN 1 ELSE 0 END as missing_title,
                CASE WHEN fm_desc.value IS NULL THEN 1 ELSE 0 END as missing_description,
                CASE WHEN t.tag IS NULL THEN 1 ELSE 0 END as missing_tags
            FROM files f
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_desc ON f.id = fm_desc.file_id AND fm_desc.key = 'description'
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE fm_title.value IS NULL OR fm_desc.value IS NULL OR t.tag IS NULL
            GROUP BY f.id, f.path
            LIMIT 50
        """
        missing_metadata_result = self.query_engine.execute_query(missing_metadata_query)
        report['files_missing_metadata'] = missing_metadata_result.rows

        # Content quality issues
        quality_issues_query = """
            SELECT
                path,
                word_count,
                heading_count,
                CASE
                    WHEN word_count < 100 THEN 'Very short content'
                    WHEN word_count > 5000 THEN 'Very long content'
                    WHEN heading_count = 0 AND word_count > 300 THEN 'No headings'
                    ELSE 'OK'
                END as issue_type
            FROM files
            WHERE word_count < 100 OR word_count > 5000 OR (heading_count = 0 AND word_count > 300)
            ORDER BY word_count DESC
            LIMIT 50
        """
        quality_issues_result = self.query_engine.execute_query(quality_issues_query)
        report['quality_issues'] = quality_issues_result.rows

        return report

    def get_aggregation_queries(self) -> Dict[str, str]:
        """
        Get predefined aggregation queries for reporting.

        Returns:
            Dictionary of query names to SQL strings for common aggregations
        """
        return {
            "files_by_directory": """
                SELECT
                    directory,
                    COUNT(*) as file_count,
                    AVG(word_count) as avg_word_count,
                    SUM(word_count) as total_words
                FROM files
                GROUP BY directory
                ORDER BY file_count DESC
            """,

            "content_by_month": """
                SELECT
                    strftime('%Y-%m', modified_date) as month,
                    COUNT(*) as files_modified,
                    SUM(word_count) as words_added
                FROM files
                WHERE modified_date >= datetime('now', '-12 months')
                GROUP BY strftime('%Y-%m', modified_date)
                ORDER BY month DESC
            """,

            "tag_cooccurrence": """
                SELECT
                    t1.tag as tag1,
                    t2.tag as tag2,
                    COUNT(*) as cooccurrence_count
                FROM tags t1
                JOIN tags t2 ON t1.file_id = t2.file_id AND t1.tag < t2.tag
                GROUP BY t1.tag, t2.tag
                HAVING COUNT(*) > 1
                ORDER BY cooccurrence_count DESC
                LIMIT 50
            """,

            "link_popularity": """
                SELECT
                    link_target,
                    COUNT(*) as incoming_links,
                    link_type,
                    is_internal
                FROM links
                GROUP BY link_target, link_type, is_internal
                ORDER BY incoming_links DESC
                LIMIT 50
            """,

            "word_count_distribution": """
                SELECT
                    CASE
                        WHEN word_count = 0 THEN '0 words'
                        WHEN word_count < 100 THEN '1-99 words'
                        WHEN word_count < 500 THEN '100-499 words'
                        WHEN word_count < 1000 THEN '500-999 words'
                        WHEN word_count < 2000 THEN '1000-1999 words'
                        ELSE '2000+ words'
                    END as word_range,
                    COUNT(*) as file_count
                FROM files
                GROUP BY
                    CASE
                        WHEN word_count = 0 THEN '0 words'
                        WHEN word_count < 100 THEN '1-99 words'
                        WHEN word_count < 500 THEN '100-499 words'
                        WHEN word_count < 1000 THEN '500-999 words'
                        WHEN word_count < 2000 THEN '1000-1999 words'
                        ELSE '2000+ words'
                    END
                ORDER BY MIN(word_count)
            """
        }

    def execute_aggregation_query(self, query_name: str) -> QueryResult:
        """
        Execute a predefined aggregation query.

        Args:
            query_name: Name of the aggregation query to execute

        Returns:
            Query result

        Raises:
            QueryError: If query name is not found
        """
        queries = self.get_aggregation_queries()
        if query_name not in queries:
            available = ', '.join(queries.keys())
            raise QueryError(f"Unknown aggregation query '{query_name}'. Available: {available}")

        return self.query_engine.execute_query(queries[query_name])