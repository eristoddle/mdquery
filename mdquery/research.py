"""
Research and synthesis features for mdquery.

This module provides advanced research capabilities including fuzzy text matching,
cross-collection querying, source attribution, and research organization features.
Extends the base functionality to support comprehensive research workflows.
"""

import sqlite3
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
import difflib
import hashlib

from .models import QueryResult
from .query import QueryEngine, QueryError

logger = logging.getLogger(__name__)


@dataclass
class FuzzyMatch:
    """Results of fuzzy text matching for content discovery."""
    file_path: str
    matched_text: str
    similarity_score: float
    context_before: str
    context_after: str
    match_type: str  # 'content', 'title', 'heading'
    line_number: Optional[int] = None


@dataclass
class CrossCollectionResult:
    """Results from cross-collection querying."""
    collection_name: str
    file_path: str
    relevance_score: float
    matched_fields: List[str]
    metadata: Dict[str, Any]


@dataclass
class SourceAttribution:
    """Source attribution information for quotes and references."""
    source_file: str
    quote_text: str
    context: str
    author: Optional[str]
    title: Optional[str]
    date: Optional[str]
    page_number: Optional[str]
    url: Optional[str]
    citation_format: str


@dataclass
class ResearchFilter:
    """Filter criteria for research organization."""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    topics: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    collections: Optional[List[str]] = None


class ResearchEngine:
    """
    Advanced research engine for content discovery and synthesis.

    Provides fuzzy matching, cross-collection querying, source attribution,
    and research organization capabilities on top of the base QueryEngine.
    """

    def __init__(self, query_engine: QueryEngine):
        """
        Initialize research engine.

        Args:
            query_engine: Base query engine instance
        """
        self.query_engine = query_engine
        self.db_manager = query_engine.db_manager

    def fuzzy_search(self, search_text: str, similarity_threshold: float = 0.6,
                    max_results: int = 50, search_fields: Optional[List[str]] = None) -> List[FuzzyMatch]:
        """
        Perform fuzzy text matching for related content discovery.

        Uses multiple algorithms including sequence matching and n-gram analysis
        to find content similar to the search text across all indexed files.

        Args:
            search_text: Text to search for similar content
            similarity_threshold: Minimum similarity score (0.0 to 1.0)
            max_results: Maximum number of results to return
            search_fields: Fields to search in ('content', 'title', 'headings')

        Returns:
            List of fuzzy matches sorted by similarity score
        """
        if not search_text.strip():
            return []

        search_fields = search_fields or ['content', 'title', 'headings']
        matches = []

        # Normalize search text
        normalized_search = self._normalize_text(search_text)
        search_words = set(normalized_search.lower().split())

        # Get all content for fuzzy matching
        query = """
            SELECT
                f.path,
                c.title,
                c.content,
                c.headings
            FROM files f
            JOIN content_fts c ON f.id = c.file_id
        """

        result = self.query_engine.execute_query(query)

        for row in result.rows:
            file_path = row['path']

            # Search in title
            if 'title' in search_fields and row['title']:
                title_matches = self._find_fuzzy_matches_in_text(
                    search_text, row['title'], similarity_threshold, 'title'
                )
                for match in title_matches:
                    matches.append(FuzzyMatch(
                        file_path=file_path,
                        matched_text=match['text'],
                        similarity_score=match['score'],
                        context_before='',
                        context_after='',
                        match_type='title'
                    ))

            # Search in content
            if 'content' in search_fields and row['content']:
                content_matches = self._find_fuzzy_matches_in_text(
                    search_text, row['content'], similarity_threshold, 'content'
                )
                for match in content_matches:
                    context = self._extract_context(row['content'], match['start'], match['end'])
                    matches.append(FuzzyMatch(
                        file_path=file_path,
                        matched_text=match['text'],
                        similarity_score=match['score'],
                        context_before=context['before'],
                        context_after=context['after'],
                        match_type='content',
                        line_number=match.get('line_number')
                    ))

            # Search in headings
            if 'headings' in search_fields and row['headings']:
                heading_matches = self._find_fuzzy_matches_in_text(
                    search_text, row['headings'], similarity_threshold, 'heading'
                )
                for match in heading_matches:
                    matches.append(FuzzyMatch(
                        file_path=file_path,
                        matched_text=match['text'],
                        similarity_score=match['score'],
                        context_before='',
                        context_after='',
                        match_type='heading'
                    ))

        # Sort by similarity score and limit results
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:max_results]

    def _normalize_text(self, text: str) -> str:
        """Normalize text for fuzzy matching."""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove markdown formatting
        text = re.sub(r'[*_`#\[\]()]+', '', text)
        return text

    def _find_fuzzy_matches_in_text(self, search_text: str, target_text: str,
                                   threshold: float, match_type: str) -> List[Dict[str, Any]]:
        """Find fuzzy matches within a text using multiple algorithms."""
        matches = []
        normalized_search = self._normalize_text(search_text)
        normalized_target = self._normalize_text(target_text)

        # Split into sentences/paragraphs for content, or use whole text for titles
        if match_type == 'content':
            segments = self._split_into_segments(normalized_target)
        else:
            segments = [{'text': normalized_target, 'start': 0, 'end': len(target_text)}]

        for segment in segments:
            segment_text = segment['text']

            # Sequence matching
            similarity = difflib.SequenceMatcher(None, normalized_search.lower(),
                                               segment_text.lower()).ratio()

            if similarity >= threshold:
                matches.append({
                    'text': segment_text,
                    'score': similarity,
                    'start': segment['start'],
                    'end': segment['end'],
                    'line_number': segment.get('line_number')
                })

            # Word overlap scoring for longer texts
            if len(segment_text.split()) > 3:
                word_similarity = self._calculate_word_overlap_similarity(
                    normalized_search, segment_text
                )
                if word_similarity >= threshold:
                    matches.append({
                        'text': segment_text,
                        'score': word_similarity,
                        'start': segment['start'],
                        'end': segment['end'],
                        'line_number': segment.get('line_number')
                    })

        # Remove duplicates and return top matches
        unique_matches = {}
        for match in matches:
            key = (match['start'], match['end'])
            if key not in unique_matches or match['score'] > unique_matches[key]['score']:
                unique_matches[key] = match

        return list(unique_matches.values())

    def _split_into_segments(self, text: str) -> List[Dict[str, Any]]:
        """Split text into segments for fuzzy matching."""
        segments = []
        lines = text.split('\n')

        current_pos = 0
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and len(line) > 20:  # Only consider substantial lines
                segments.append({
                    'text': line,
                    'start': current_pos,
                    'end': current_pos + len(line),
                    'line_number': line_num
                })
            current_pos += len(line) + 1  # +1 for newline

        return segments

    def _calculate_word_overlap_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _extract_context(self, text: str, start: int, end: int,
                        context_chars: int = 100) -> Dict[str, str]:
        """Extract context around a match."""
        before_start = max(0, start - context_chars)
        after_end = min(len(text), end + context_chars)

        return {
            'before': text[before_start:start].strip(),
            'after': text[end:after_end].strip()
        }

    def cross_collection_search(self, query_text: str, collections: List[str],
                              max_results_per_collection: int = 20) -> List[CrossCollectionResult]:
        """
        Perform cross-collection querying for multiple note sources.

        Searches across different collections (directories or source types)
        and returns unified results with relevance scoring.

        Args:
            query_text: Text to search for across collections
            collections: List of collection identifiers (directory paths)
            max_results_per_collection: Maximum results per collection

        Returns:
            List of cross-collection results with relevance scores
        """
        results = []

        for collection in collections:
            collection_results = self._search_in_collection(
                query_text, collection, max_results_per_collection
            )
            results.extend(collection_results)

        # Sort by relevance score across all collections
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results

    def _search_in_collection(self, query_text: str, collection: str,
                            max_results: int) -> List[CrossCollectionResult]:
        """Search within a specific collection."""
        # Use FTS5 for initial search within collection
        fts_query = """
            SELECT
                f.path,
                f.directory,
                c.title,
                c.content,
                snippet(content_fts, 2, '<mark>', '</mark>', '...', 32) as snippet,
                bm25(content_fts) as rank
            FROM files f
            JOIN content_fts c ON f.id = c.file_id
            WHERE f.directory LIKE ? AND content_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """

        # Prepare FTS5 query
        fts_search_text = self._prepare_fts_query(query_text)
        collection_pattern = f"{collection}%"

        try:
            result = self.query_engine.execute_query(
                fts_query, [collection_pattern, fts_search_text, max_results]
            )
        except QueryError:
            # Fallback to LIKE search if FTS5 query fails
            return self._fallback_collection_search(query_text, collection, max_results)

        collection_results = []
        for row in result.rows:
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(query_text, row)

            # Identify matched fields
            matched_fields = self._identify_matched_fields(query_text, row)

            # Get additional metadata
            metadata = self._get_file_metadata(row['path'])

            collection_results.append(CrossCollectionResult(
                collection_name=collection,
                file_path=row['path'],
                relevance_score=relevance_score,
                matched_fields=matched_fields,
                metadata=metadata
            ))

        return collection_results

    def _prepare_fts_query(self, query_text: str) -> str:
        """Prepare text for FTS5 query."""
        # Clean and tokenize
        words = re.findall(r'\w+', query_text.lower())

        # Create FTS5 query with OR logic for flexibility
        if len(words) == 1:
            return words[0]
        else:
            return ' OR '.join(words)

    def _fallback_collection_search(self, query_text: str, collection: str,
                                  max_results: int) -> List[CrossCollectionResult]:
        """Fallback search using LIKE when FTS5 fails."""
        like_query = """
            SELECT
                f.path,
                f.directory,
                c.title,
                c.content
            FROM files f
            JOIN content_fts c ON f.id = c.file_id
            WHERE f.directory LIKE ? AND (
                c.title LIKE ? OR c.content LIKE ?
            )
            LIMIT ?
        """

        search_pattern = f"%{query_text}%"
        collection_pattern = f"{collection}%"

        result = self.query_engine.execute_query(
            like_query, [collection_pattern, search_pattern, search_pattern, max_results]
        )

        collection_results = []
        for row in result.rows:
            relevance_score = self._calculate_relevance_score(query_text, row)
            matched_fields = self._identify_matched_fields(query_text, row)
            metadata = self._get_file_metadata(row['path'])

            collection_results.append(CrossCollectionResult(
                collection_name=collection,
                file_path=row['path'],
                relevance_score=relevance_score,
                matched_fields=matched_fields,
                metadata=metadata
            ))

        return collection_results

    def _calculate_relevance_score(self, query_text: str, row: Dict[str, Any]) -> float:
        """Calculate relevance score for search results."""
        score = 0.0
        query_words = set(query_text.lower().split())

        # Title match (highest weight)
        title = row.get('title', '') or ''
        title_words = set(title.lower().split())
        title_overlap = len(query_words.intersection(title_words))
        if title_words:
            score += (title_overlap / len(title_words)) * 3.0

        # Content match
        content = row.get('content', '') or ''
        content_words = set(content.lower().split())
        if content_words:
            content_overlap = len(query_words.intersection(content_words))
            score += (content_overlap / len(content_words)) * 1.0

        # BM25 rank if available
        if 'rank' in row and row['rank'] is not None:
            # Normalize BM25 score (higher is better, but scale varies)
            score += min(row['rank'] / 10.0, 2.0)

        return score

    def _identify_matched_fields(self, query_text: str, row: Dict[str, Any]) -> List[str]:
        """Identify which fields contain matches."""
        matched_fields = []
        query_lower = query_text.lower()

        if row.get('title') and query_lower in row['title'].lower():
            matched_fields.append('title')

        if row.get('content') and query_lower in row['content'].lower():
            matched_fields.append('content')

        return matched_fields

    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get additional metadata for a file."""
        metadata_query = """
            SELECT
                f.modified_date,
                f.word_count,
                fm_author.value as author,
                fm_category.value as category,
                GROUP_CONCAT(t.tag) as tags
            FROM files f
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
            LEFT JOIN tags t ON f.id = t.file_id
            WHERE f.path = ?
            GROUP BY f.id
        """

        result = self.query_engine.execute_query(metadata_query, [file_path])
        if result.rows:
            row = result.rows[0]
            return {
                'modified_date': row['modified_date'],
                'word_count': row['word_count'],
                'author': row['author'],
                'category': row['category'],
                'tags': row['tags'].split(',') if row['tags'] else []
            }
        return {}

    def extract_quotes_with_attribution(self, file_paths: Optional[List[str]] = None,
                                      quote_patterns: Optional[List[str]] = None) -> List[SourceAttribution]:
        """
        Extract quotes and references with source attribution preservation.

        Identifies quoted text, citations, and references while preserving
        source attribution information for proper citation.

        Args:
            file_paths: Optional list of files to process
            quote_patterns: Custom regex patterns for quote detection

        Returns:
            List of source attributions with quote and citation information
        """
        default_patterns = [
            r'"([^"]{20,})"',  # Double quoted text (min 20 chars)
            r'> (.+)',  # Blockquotes
            r'(?:According to|As stated by|.*notes that)\s+(.+)',  # Attribution phrases
            r'\[([^\]]+)\]\([^)]+\)',  # Markdown links as potential citations
        ]

        patterns = quote_patterns or default_patterns
        attributions = []

        # Get files with content
        if file_paths:
            placeholders = ','.join('?' * len(file_paths))
            query = f"""
                SELECT
                    f.path,
                    c.content,
                    c.title,
                    fm_author.value as author,
                    fm_date.value as date,
                    fm_url.value as url
                FROM files f
                JOIN content_fts c ON f.id = c.file_id
                LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
                LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
                LEFT JOIN frontmatter fm_url ON f.id = fm_url.file_id AND fm_url.key = 'url'
                WHERE f.path IN ({placeholders})
            """
            result = self.query_engine.execute_query(query, file_paths)
        else:
            query = """
                SELECT
                    f.path,
                    c.content,
                    c.title,
                    fm_author.value as author,
                    fm_date.value as date,
                    fm_url.value as url
                FROM files f
                JOIN content_fts c ON f.id = c.file_id
                LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
                LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
                LEFT JOIN frontmatter fm_url ON f.id = fm_url.file_id AND fm_url.key = 'url'
            """
            result = self.query_engine.execute_query(query)

        for row in result.rows:
            file_attributions = self._extract_quotes_from_content(
                row['path'], row['content'], patterns, {
                    'title': row['title'],
                    'author': row['author'],
                    'date': row['date'],
                    'url': row['url']
                }
            )
            attributions.extend(file_attributions)

        return attributions

    def _extract_quotes_from_content(self, file_path: str, content: str,
                                   patterns: List[str], metadata: Dict[str, Any]) -> List[SourceAttribution]:
        """Extract quotes from content using patterns."""
        attributions = []

        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)

            for match in matches:
                quote_text = match.group(1) if match.groups() else match.group(0)

                # Extract context around the quote
                start_pos = max(0, match.start() - 200)
                end_pos = min(len(content), match.end() + 200)
                context = content[start_pos:end_pos].strip()

                # Generate citation format
                citation = self._generate_citation(file_path, metadata, quote_text)

                attributions.append(SourceAttribution(
                    source_file=file_path,
                    quote_text=quote_text.strip(),
                    context=context,
                    author=metadata.get('author'),
                    title=metadata.get('title'),
                    date=metadata.get('date'),
                    page_number=None,  # Could be extracted from context if available
                    url=metadata.get('url'),
                    citation_format=citation
                ))

        return attributions

    def _generate_citation(self, file_path: str, metadata: Dict[str, Any], quote_text: str) -> str:
        """Generate citation format for a quote."""
        author = metadata.get('author', 'Unknown Author')
        title = metadata.get('title', Path(file_path).stem)
        date = metadata.get('date', 'n.d.')

        # Simple APA-style citation
        citation = f"{author} ({date}). {title}."

        if metadata.get('url'):
            citation += f" Retrieved from {metadata['url']}"
        else:
            citation += f" Source: {file_path}"

        return citation

    def filter_by_research_criteria(self, research_filter: ResearchFilter) -> QueryResult:
        """
        Filter content by research criteria including date ranges and topics.

        Provides advanced filtering for research organization based on
        multiple criteria including dates, topics, sources, and authors.

        Args:
            research_filter: Filter criteria for research organization

        Returns:
            QueryResult with filtered content matching criteria
        """
        # Build dynamic query based on filter criteria
        base_query = """
            SELECT DISTINCT
                f.path,
                f.filename,
                f.directory,
                f.modified_date,
                f.word_count,
                c.title,
                fm_author.value as author,
                fm_category.value as category,
                fm_date.value as date,
                GROUP_CONCAT(DISTINCT t.tag) as tags
            FROM files f
            JOIN content_fts c ON f.id = c.file_id
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            LEFT JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
            LEFT JOIN frontmatter fm_date ON f.id = fm_date.file_id AND fm_date.key = 'date'
            LEFT JOIN tags t ON f.id = t.file_id
        """

        conditions = []
        params = []

        # Date range filtering
        if research_filter.date_from:
            conditions.append("f.modified_date >= ?")
            params.append(research_filter.date_from.isoformat())

        if research_filter.date_to:
            conditions.append("f.modified_date <= ?")
            params.append(research_filter.date_to.isoformat())

        # Topic filtering (tags and categories)
        if research_filter.topics:
            topic_conditions = []
            for topic in research_filter.topics:
                topic_conditions.append("(t.tag LIKE ? OR fm_category.value LIKE ?)")
                params.extend([f"%{topic}%", f"%{topic}%"])
            conditions.append(f"({' OR '.join(topic_conditions)})")

        # Source filtering (file paths or directories)
        if research_filter.sources:
            source_conditions = []
            for source in research_filter.sources:
                source_conditions.append("f.path LIKE ?")
                params.append(f"%{source}%")
            conditions.append(f"({' OR '.join(source_conditions)})")

        # Author filtering
        if research_filter.authors:
            author_conditions = []
            for author in research_filter.authors:
                author_conditions.append("fm_author.value LIKE ?")
                params.append(f"%{author}%")
            conditions.append(f"({' OR '.join(author_conditions)})")

        # Collection filtering (directories)
        if research_filter.collections:
            collection_conditions = []
            for collection in research_filter.collections:
                collection_conditions.append("f.directory LIKE ?")
                params.append(f"{collection}%")
            conditions.append(f"({' OR '.join(collection_conditions)})")

        # File type filtering
        if research_filter.file_types:
            type_conditions = []
            for file_type in research_filter.file_types:
                type_conditions.append("f.filename LIKE ?")
                params.append(f"%.{file_type}")
            conditions.append(f"({' OR '.join(type_conditions)})")

        # Combine query
        if conditions:
            query = f"{base_query} WHERE {' AND '.join(conditions)} GROUP BY f.id ORDER BY f.modified_date DESC"
        else:
            query = f"{base_query} GROUP BY f.id ORDER BY f.modified_date DESC"

        return self.query_engine.execute_query(query, params)

    def generate_research_summary(self, research_filter: Optional[ResearchFilter] = None) -> Dict[str, Any]:
        """
        Generate comprehensive research summary and statistics.

        Provides overview of research content including source distribution,
        temporal patterns, topic analysis, and content metrics.

        Args:
            research_filter: Optional filter to scope the summary

        Returns:
            Dictionary containing research summary statistics
        """
        summary = {}

        # Get filtered results if filter provided
        if research_filter:
            filtered_result = self.filter_by_research_criteria(research_filter)
            file_paths = [row['path'] for row in filtered_result.rows]

            # Create temporary view for filtered analysis
            if file_paths:
                placeholders = ','.join('?' * len(file_paths))
                path_filter = f"WHERE f.path IN ({placeholders})"
                filter_params = file_paths
            else:
                path_filter = "WHERE 1=0"  # No results
                filter_params = []
        else:
            path_filter = ""
            filter_params = []

        # Basic statistics
        stats_query = f"""
            SELECT
                COUNT(DISTINCT f.id) as total_files,
                COUNT(DISTINCT f.directory) as total_collections,
                COUNT(DISTINCT fm_author.value) as total_authors,
                AVG(f.word_count) as avg_word_count,
                SUM(f.word_count) as total_words,
                MIN(f.modified_date) as earliest_date,
                MAX(f.modified_date) as latest_date
            FROM files f
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            {path_filter}
        """

        stats_result = self.query_engine.execute_query(stats_query, filter_params)
        summary['basic_stats'] = stats_result.rows[0] if stats_result.rows else {}

        # Source distribution
        source_query = f"""
            SELECT
                f.directory as collection,
                COUNT(*) as file_count,
                AVG(f.word_count) as avg_words,
                COUNT(DISTINCT fm_author.value) as author_count
            FROM files f
            LEFT JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            {path_filter}
            GROUP BY f.directory
            ORDER BY file_count DESC
        """

        source_result = self.query_engine.execute_query(source_query, filter_params)
        summary['source_distribution'] = source_result.rows

        # Topic analysis (top tags and categories)
        topic_query = f"""
            SELECT
                t.tag as topic,
                COUNT(*) as frequency,
                'tag' as type
            FROM files f
            JOIN tags t ON f.id = t.file_id
            {path_filter}
            GROUP BY t.tag

            UNION ALL

            SELECT
                fm_category.value as topic,
                COUNT(*) as frequency,
                'category' as type
            FROM files f
            JOIN frontmatter fm_category ON f.id = fm_category.file_id AND fm_category.key = 'category'
            {path_filter}
            GROUP BY fm_category.value

            ORDER BY frequency DESC
            LIMIT 20
        """

        topic_result = self.query_engine.execute_query(topic_query, filter_params)
        summary['topic_analysis'] = topic_result.rows

        # Temporal patterns (content by month)
        temporal_query = f"""
            SELECT
                strftime('%Y-%m', f.modified_date) as month,
                COUNT(*) as files_count,
                SUM(f.word_count) as words_count
            FROM files f
            {path_filter}
            GROUP BY strftime('%Y-%m', f.modified_date)
            ORDER BY month DESC
            LIMIT 12
        """

        temporal_result = self.query_engine.execute_query(temporal_query, filter_params)
        summary['temporal_patterns'] = temporal_result.rows

        # Author productivity
        author_query = f"""
            SELECT
                fm_author.value as author,
                COUNT(*) as file_count,
                SUM(f.word_count) as total_words,
                AVG(f.word_count) as avg_words_per_file
            FROM files f
            JOIN frontmatter fm_author ON f.id = fm_author.file_id AND fm_author.key = 'author'
            {path_filter}
            GROUP BY fm_author.value
            ORDER BY file_count DESC
            LIMIT 10
        """

        author_result = self.query_engine.execute_query(author_query, filter_params)
        summary['author_productivity'] = author_result.rows

        return summary