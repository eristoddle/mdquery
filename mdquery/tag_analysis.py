"""
Comprehensive tag analysis engine for mdquery.

This module provides advanced tag analysis capabilities including hierarchical tag support,
semantic content grouping, actionable vs theoretical insight classification, and content
quality filtering to focus on substantive information.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
from pathlib import Path
import json

from .models import QueryResult
from .query import QueryEngine
from .exceptions import MdqueryError

logger = logging.getLogger(__name__)


@dataclass
class TopicGroup:
    """Represents a group of content organized by topic."""
    name: str
    documents: List[Dict[str, Any]]
    key_themes: List[str]
    related_groups: List[str]
    tag_patterns: List[str]
    content_quality_score: float


@dataclass
class ActionableInsight:
    """Represents a practical, implementable recommendation."""
    title: str
    description: str
    implementation_difficulty: str  # "low", "medium", "high"
    expected_impact: str  # "low", "medium", "high"
    category: str  # "process", "tools", "automation", "quality"
    source_files: List[str]
    confidence_score: float


@dataclass
class TheoreticalInsight:
    """Represents conceptual insights and patterns."""
    title: str
    description: str
    related_concepts: List[str]
    research_directions: List[str]
    source_files: List[str]
    confidence_score: float


@dataclass
class TagAnalysisResult:
    """Complete tag analysis results."""
    topic_groups: List[TopicGroup]
    actionable_insights: List[ActionableInsight]
    theoretical_insights: List[TheoreticalInsight]
    tag_hierarchy: Dict[str, List[str]]
    content_statistics: Dict[str, Any]
    quality_metrics: Dict[str, float]


class TagAnalysisEngine:
    """
    Advanced tag analysis engine for comprehensive content analysis.

    Provides hierarchical tag analysis, semantic content grouping,
    actionable vs theoretical insight classification, and quality filtering.
    """

    def __init__(self, query_engine: QueryEngine):
        """Initialize tag analysis engine."""
        self.query_engine = query_engine

        # Actionable keywords that indicate practical content
        self.actionable_keywords = {
            'implement', 'build', 'create', 'setup', 'configure', 'install',
            'deploy', 'test', 'debug', 'fix', 'optimize', 'improve', 'refactor',
            'tutorial', 'guide', 'howto', 'step', 'process', 'workflow',
            'tool', 'script', 'automation', 'integration', 'api', 'framework',
            'best practice', 'pattern', 'solution', 'approach', 'method'
        }

        # Theoretical keywords that indicate conceptual content
        self.theoretical_keywords = {
            'theory', 'concept', 'principle', 'philosophy', 'research',
            'analysis', 'study', 'review', 'overview', 'introduction',
            'background', 'history', 'evolution', 'future', 'trend',
            'comparison', 'evaluation', 'assessment', 'discussion',
            'exploration', 'investigation', 'understanding', 'insight'
        }

        # Fluff indicators - content that may be less substantive
        self.fluff_indicators = {
            'personal note', 'random thought', 'quick note', 'reminder',
            'todo', 'draft', 'placeholder', 'template', 'example only',
            'test', 'scratch', 'temporary', 'wip', 'work in progress'
        }

    def comprehensive_tag_analysis(
        self,
        tag_patterns: List[str],
        grouping_strategy: str = "semantic",
        include_actionable: bool = True,
        include_theoretical: bool = True,
        remove_fluff: bool = True,
        min_content_quality: float = 0.3
    ) -> TagAnalysisResult:
        """
        Perform comprehensive tag analysis with intelligent content grouping.

        Args:
            tag_patterns: List of tag patterns to analyze (supports wildcards and hierarchical tags)
            grouping_strategy: Strategy for grouping content ("semantic", "tag-hierarchy", "temporal")
            include_actionable: Whether to include actionable insights
            include_theoretical: Whether to include theoretical insights
            remove_fluff: Whether to filter out low-quality content
            min_content_quality: Minimum content quality score (0.0 to 1.0)

        Returns:
            TagAnalysisResult with comprehensive analysis
        """
        logger.info(f"Starting comprehensive tag analysis for patterns: {tag_patterns}")

        # Get matching content based on tag patterns
        matching_content = self._get_matching_content(tag_patterns)

        if not matching_content:
            logger.warning(f"No content found matching tag patterns: {tag_patterns}")
            return TagAnalysisResult(
                topic_groups=[],
                actionable_insights=[],
                theoretical_insights=[],
                tag_hierarchy={},
                content_statistics={},
                quality_metrics={}
            )

        # Filter content quality if requested
        if remove_fluff:
            matching_content = self._filter_content_quality(matching_content, min_content_quality)

        # Build tag hierarchy
        tag_hierarchy = self._build_tag_hierarchy(matching_content)

        # Group content by strategy
        topic_groups = self._group_content(matching_content, grouping_strategy, tag_hierarchy)

        # Extract insights
        actionable_insights = []
        theoretical_insights = []

        if include_actionable:
            actionable_insights = self._extract_actionable_insights(matching_content, topic_groups)

        if include_theoretical:
            theoretical_insights = self._extract_theoretical_insights(matching_content, topic_groups)

        # Calculate statistics and metrics
        content_statistics = self._calculate_content_statistics(matching_content)
        quality_metrics = self._calculate_quality_metrics(matching_content, topic_groups)

        return TagAnalysisResult(
            topic_groups=topic_groups,
            actionable_insights=actionable_insights,
            theoretical_insights=theoretical_insights,
            tag_hierarchy=tag_hierarchy,
            content_statistics=content_statistics,
            quality_metrics=quality_metrics
        )

    def _get_matching_content(self, tag_patterns: List[str]) -> List[Dict[str, Any]]:
        """Get content matching the specified tag patterns."""
        # Build SQL query to match tag patterns
        tag_conditions = []
        params = []

        for pattern in tag_patterns:
            if '*' in pattern or '?' in pattern:
                # Wildcard pattern
                sql_pattern = pattern.replace('*', '%').replace('?', '_')
                tag_conditions.append("t.tag LIKE ?")
                params.append(sql_pattern)
            elif '/' in pattern:
                # Hierarchical tag pattern
                tag_conditions.append("t.tag LIKE ?")
                params.append(f"{pattern}%")
            else:
                # Exact tag match
                tag_conditions.append("t.tag = ?")
                params.append(pattern)

        if not tag_conditions:
            return []

        # Query to get files with matching tags and their content
        query = f"""
            SELECT DISTINCT
                f.id,
                f.path,
                f.word_count,
                f.heading_count,
                f.created_date,
                f.modified_date,
                c.content,
                c.headings,
                GROUP_CONCAT(DISTINCT t.tag) as all_tags,
                GROUP_CONCAT(DISTINCT fm_title.value) as title,
                GROUP_CONCAT(DISTINCT fm_desc.value) as description,
                GROUP_CONCAT(DISTINCT fm_cat.value) as category
            FROM files f
            JOIN tags t ON f.id = t.file_id
            LEFT JOIN content_fts c ON f.id = c.file_id
            LEFT JOIN frontmatter fm_title ON f.id = fm_title.file_id AND fm_title.key = 'title'
            LEFT JOIN frontmatter fm_desc ON f.id = fm_desc.file_id AND fm_desc.key = 'description'
            LEFT JOIN frontmatter fm_cat ON f.id = fm_cat.file_id AND fm_cat.key = 'category'
            WHERE ({' OR '.join(tag_conditions)})
            GROUP BY f.id, f.path, f.word_count, f.heading_count, f.created_date, f.modified_date, c.content, c.headings
            ORDER BY f.modified_date DESC
        """

        result = self.query_engine.execute_query(query, params)

        # Process results into structured format
        content_list = []
        for row in result.rows:
            tags = [tag.strip() for tag in (row.get('all_tags') or '').split(',') if tag.strip()]

            content_item = {
                'id': row['id'],
                'path': row['path'],
                'word_count': row.get('word_count', 0),
                'heading_count': row.get('heading_count', 0),
                'created_date': row.get('created_date'),
                'modified_date': row.get('modified_date'),
                'content': row.get('content', ''),
                'headings': row.get('headings', ''),
                'tags': tags,
                'title': row.get('title'),
                'description': row.get('description'),
                'category': row.get('category')
            }
            content_list.append(content_item)

        logger.info(f"Found {len(content_list)} files matching tag patterns")
        return content_list

    def _filter_content_quality(self, content_list: List[Dict[str, Any]], min_quality: float) -> List[Dict[str, Any]]:
        """Filter content based on quality metrics to remove fluff."""
        filtered_content = []

        for item in content_list:
            quality_score = self._calculate_content_quality_score(item)

            if quality_score >= min_quality:
                item['quality_score'] = quality_score
                filtered_content.append(item)
            else:
                logger.debug(f"Filtered out low-quality content: {item['path']} (score: {quality_score:.2f})")

        logger.info(f"Quality filtering: {len(filtered_content)}/{len(content_list)} files passed quality threshold")
        return filtered_content

    def _calculate_content_quality_score(self, content_item: Dict[str, Any]) -> float:
        """Calculate quality score for a content item."""
        score = 1.0
        content = content_item.get('content', '').lower()
        title = (content_item.get('title') or '').lower()
        tags = [tag.lower() for tag in content_item.get('tags', [])]

        # Check for fluff indicators
        fluff_count = 0
        for indicator in self.fluff_indicators:
            if indicator in content or indicator in title or any(indicator in tag for tag in tags):
                fluff_count += 1

        if fluff_count > 0:
            score -= 0.2 * fluff_count

        # Word count factor
        word_count = content_item.get('word_count', 0)
        if word_count < 50:
            score -= 0.4  # Very short content
        elif word_count < 100:
            score -= 0.2  # Short content
        elif word_count > 2000:
            score += 0.1  # Substantial content

        # Heading structure factor
        heading_count = content_item.get('heading_count', 0)
        if heading_count > 0 and word_count > 200:
            score += 0.1  # Well-structured content

        # Tag quality factor
        tag_count = len(content_item.get('tags', []))
        if tag_count >= 2:
            score += 0.1  # Well-tagged content
        elif tag_count == 0:
            score -= 0.1  # Untagged content

        # Metadata completeness
        if content_item.get('title'):
            score += 0.05
        if content_item.get('description'):
            score += 0.05

        return max(0.0, min(1.0, score))

    def _build_tag_hierarchy(self, content_list: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Build hierarchical tag structure from content."""
        hierarchy = defaultdict(list)
        all_tags = set()

        # Collect all tags
        for item in content_list:
            all_tags.update(item.get('tags', []))

        # Build hierarchy based on '/' separator
        for tag in all_tags:
            if '/' in tag:
                parts = tag.split('/')
                for i in range(len(parts) - 1):
                    parent = '/'.join(parts[:i+1])
                    child = '/'.join(parts[:i+2])
                    if child not in hierarchy[parent]:
                        hierarchy[parent].append(child)
            else:
                # Top-level tag
                if tag not in hierarchy:
                    hierarchy[tag] = []

        return dict(hierarchy)

    def _group_content(self, content_list: List[Dict[str, Any]], strategy: str,
                      tag_hierarchy: Dict[str, List[str]]) -> List[TopicGroup]:
        """Group content based on the specified strategy."""
        if strategy == "semantic":
            return self._group_by_semantic_similarity(content_list)
        elif strategy == "tag-hierarchy":
            return self._group_by_tag_hierarchy(content_list, tag_hierarchy)
        elif strategy == "temporal":
            return self._group_by_temporal_patterns(content_list)
        else:
            # Default to semantic grouping
            return self._group_by_semantic_similarity(content_list)

    def _group_by_semantic_similarity(self, content_list: List[Dict[str, Any]]) -> List[TopicGroup]:
        """Group content by semantic similarity using tag co-occurrence and content analysis."""
        # Create tag co-occurrence matrix
        tag_cooccurrence = defaultdict(lambda: defaultdict(int))
        tag_to_files = defaultdict(list)

        for item in content_list:
            tags = item.get('tags', [])
            file_id = item['id']

            # Record tag co-occurrences
            for i, tag1 in enumerate(tags):
                tag_to_files[tag1].append(item)
                for tag2 in tags[i+1:]:
                    tag_cooccurrence[tag1][tag2] += 1
                    tag_cooccurrence[tag2][tag1] += 1

        # Find tag clusters using simple clustering
        processed_tags = set()
        groups = []

        for tag in sorted(tag_to_files.keys(), key=lambda t: len(tag_to_files[t]), reverse=True):
            if tag in processed_tags:
                continue

            # Find related tags
            related_tags = {tag}
            for related_tag, count in tag_cooccurrence[tag].items():
                if count >= 2 and related_tag not in processed_tags:  # Threshold for relatedness
                    related_tags.add(related_tag)

            # Collect all files with these tags
            group_files = []
            seen_files = set()

            for group_tag in related_tags:
                for file_item in tag_to_files[group_tag]:
                    if file_item['id'] not in seen_files:
                        group_files.append(file_item)
                        seen_files.add(file_item['id'])

            if group_files:
                # Generate group name and themes
                group_name = self._generate_group_name(related_tags, group_files)
                key_themes = self._extract_key_themes(group_files)
                quality_score = sum(item.get('quality_score', 0.5) for item in group_files) / len(group_files)

                group = TopicGroup(
                    name=group_name,
                    documents=group_files,
                    key_themes=key_themes,
                    related_groups=[],  # Will be populated later
                    tag_patterns=list(related_tags),
                    content_quality_score=quality_score
                )
                groups.append(group)
                processed_tags.update(related_tags)

        # Sort groups by quality and size
        groups.sort(key=lambda g: (g.content_quality_score, len(g.documents)), reverse=True)

        return groups

    def _group_by_tag_hierarchy(self, content_list: List[Dict[str, Any]],
                               tag_hierarchy: Dict[str, List[str]]) -> List[TopicGroup]:
        """Group content by hierarchical tag structure."""
        groups = []
        processed_files = set()

        # Group by top-level tags first
        top_level_tags = [tag for tag in tag_hierarchy.keys() if '/' not in tag]

        for top_tag in top_level_tags:
            # Find all files with this top-level tag or its children
            matching_files = []
            related_tags = {top_tag}

            # Add child tags
            def collect_children(parent_tag):
                children = tag_hierarchy.get(parent_tag, [])
                for child in children:
                    related_tags.add(child)
                    collect_children(child)

            collect_children(top_tag)

            # Collect files
            for item in content_list:
                if item['id'] not in processed_files:
                    item_tags = set(item.get('tags', []))
                    if item_tags.intersection(related_tags):
                        matching_files.append(item)
                        processed_files.add(item['id'])

            if matching_files:
                key_themes = self._extract_key_themes(matching_files)
                quality_score = sum(item.get('quality_score', 0.5) for item in matching_files) / len(matching_files)

                group = TopicGroup(
                    name=top_tag.replace('/', ' → '),
                    documents=matching_files,
                    key_themes=key_themes,
                    related_groups=[],
                    tag_patterns=list(related_tags),
                    content_quality_score=quality_score
                )
                groups.append(group)

        return groups

    def _group_by_temporal_patterns(self, content_list: List[Dict[str, Any]]) -> List[TopicGroup]:
        """Group content by temporal patterns (creation/modification dates)."""
        # Simple temporal grouping by month
        from datetime import datetime

        temporal_groups = defaultdict(list)

        for item in content_list:
            modified_date = item.get('modified_date')
            if modified_date:
                try:
                    date_obj = datetime.fromisoformat(modified_date.replace('Z', '+00:00'))
                    month_key = date_obj.strftime('%Y-%m')
                    temporal_groups[month_key].append(item)
                except (ValueError, AttributeError):
                    temporal_groups['unknown'].append(item)
            else:
                temporal_groups['unknown'].append(item)

        groups = []
        for month_key, files in temporal_groups.items():
            if len(files) >= 2:  # Only create groups with multiple files
                key_themes = self._extract_key_themes(files)
                quality_score = sum(item.get('quality_score', 0.5) for item in files) / len(files)

                group = TopicGroup(
                    name=f"Content from {month_key}" if month_key != 'unknown' else "Undated Content",
                    documents=files,
                    key_themes=key_themes,
                    related_groups=[],
                    tag_patterns=[],
                    content_quality_score=quality_score
                )
                groups.append(group)

        return groups

    def _generate_group_name(self, tags: Set[str], files: List[Dict[str, Any]]) -> str:
        """Generate a descriptive name for a topic group."""
        # Use the most common tag as base name
        tag_counts = Counter()
        for file_item in files:
            for tag in file_item.get('tags', []):
                if tag in tags:
                    tag_counts[tag] += 1

        if tag_counts:
            primary_tag = tag_counts.most_common(1)[0][0]
            return primary_tag.replace('/', ' → ').title()
        else:
            return "Mixed Topics"

    def _extract_key_themes(self, files: List[Dict[str, Any]]) -> List[str]:
        """Extract key themes from a group of files."""
        # Combine all tags and find most common ones
        all_tags = []
        for file_item in files:
            all_tags.extend(file_item.get('tags', []))

        tag_counts = Counter(all_tags)

        # Get top themes, but limit to reasonable number
        top_themes = [tag for tag, count in tag_counts.most_common(5) if count >= 2]

        return top_themes

    def _extract_actionable_insights(self, content_list: List[Dict[str, Any]],
                                   topic_groups: List[TopicGroup]) -> List[ActionableInsight]:
        """Extract actionable insights from content."""
        insights = []

        for item in content_list:
            content = item.get('content', '').lower()
            title = (item.get('title') or '').lower()

            # Check for actionable keywords
            actionable_score = 0
            matched_keywords = []

            for keyword in self.actionable_keywords:
                if keyword in content or keyword in title:
                    actionable_score += 1
                    matched_keywords.append(keyword)

            if actionable_score >= 2:  # Threshold for actionable content
                # Determine category based on content
                category = self._determine_insight_category(content, title, item.get('tags', []))

                # Estimate implementation difficulty
                difficulty = self._estimate_implementation_difficulty(content, matched_keywords)

                # Estimate impact
                impact = self._estimate_impact(content, item.get('tags', []))

                insight = ActionableInsight(
                    title=item.get('title') or Path(item['path']).stem,
                    description=self._extract_insight_description(content, matched_keywords),
                    implementation_difficulty=difficulty,
                    expected_impact=impact,
                    category=category,
                    source_files=[item['path']],
                    confidence_score=min(1.0, actionable_score / 5.0)
                )
                insights.append(insight)

        # Sort by confidence and impact
        insights.sort(key=lambda x: (x.confidence_score, x.expected_impact == 'high'), reverse=True)

        return insights[:20]  # Limit to top 20 insights

    def _extract_theoretical_insights(self, content_list: List[Dict[str, Any]],
                                    topic_groups: List[TopicGroup]) -> List[TheoreticalInsight]:
        """Extract theoretical insights from content."""
        insights = []

        for item in content_list:
            content = item.get('content', '').lower()
            title = (item.get('title') or '').lower()

            # Check for theoretical keywords
            theoretical_score = 0
            matched_keywords = []

            for keyword in self.theoretical_keywords:
                if keyword in content or keyword in title:
                    theoretical_score += 1
                    matched_keywords.append(keyword)

            if theoretical_score >= 2:  # Threshold for theoretical content
                # Extract related concepts
                related_concepts = self._extract_related_concepts(content, item.get('tags', []))

                # Suggest research directions
                research_directions = self._suggest_research_directions(content, matched_keywords)

                insight = TheoreticalInsight(
                    title=item.get('title') or Path(item['path']).stem,
                    description=self._extract_theoretical_description(content, matched_keywords),
                    related_concepts=related_concepts,
                    research_directions=research_directions,
                    source_files=[item['path']],
                    confidence_score=min(1.0, theoretical_score / 5.0)
                )
                insights.append(insight)

        # Sort by confidence
        insights.sort(key=lambda x: x.confidence_score, reverse=True)

        return insights[:15]  # Limit to top 15 insights

    def _determine_insight_category(self, content: str, title: str, tags: List[str]) -> str:
        """Determine the category of an actionable insight."""
        content_lower = content.lower()
        title_lower = title.lower()
        tags_lower = [tag.lower() for tag in tags]

        # Category keywords
        categories = {
            'process': ['workflow', 'process', 'methodology', 'approach', 'procedure'],
            'tools': ['tool', 'software', 'application', 'utility', 'framework', 'library'],
            'automation': ['automation', 'script', 'automated', 'ci/cd', 'pipeline', 'deploy'],
            'quality': ['quality', 'testing', 'review', 'standards', 'best practice', 'optimization']
        }

        category_scores = {}
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in content_lower or keyword in title_lower:
                    score += 1
                if any(keyword in tag for tag in tags_lower):
                    score += 2
            category_scores[category] = score

        # Return category with highest score, default to 'process'
        return max(category_scores.items(), key=lambda x: x[1])[0] if category_scores else 'process'

    def _estimate_implementation_difficulty(self, content: str, keywords: List[str]) -> str:
        """Estimate implementation difficulty based on content analysis."""
        difficulty_indicators = {
            'low': ['simple', 'easy', 'quick', 'basic', 'straightforward'],
            'high': ['complex', 'advanced', 'difficult', 'challenging', 'enterprise', 'scale']
        }

        low_score = sum(1 for indicator in difficulty_indicators['low'] if indicator in content)
        high_score = sum(1 for indicator in difficulty_indicators['high'] if indicator in content)

        if high_score > low_score:
            return 'high'
        elif low_score > 0:
            return 'low'
        else:
            return 'medium'

    def _estimate_impact(self, content: str, tags: List[str]) -> str:
        """Estimate expected impact based on content and tags."""
        high_impact_indicators = ['productivity', 'efficiency', 'performance', 'scalability', 'security']

        impact_score = 0
        for indicator in high_impact_indicators:
            if indicator in content.lower():
                impact_score += 1
            if any(indicator in tag.lower() for tag in tags):
                impact_score += 1

        if impact_score >= 3:
            return 'high'
        elif impact_score >= 1:
            return 'medium'
        else:
            return 'low'

    def _extract_insight_description(self, content: str, keywords: List[str]) -> str:
        """Extract a concise description of the actionable insight."""
        # Find sentences containing actionable keywords
        sentences = re.split(r'[.!?]+', content)
        relevant_sentences = []

        for sentence in sentences[:10]:  # Check first 10 sentences
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in keywords):
                relevant_sentences.append(sentence)

        if relevant_sentences:
            # Return first relevant sentence, truncated if too long
            description = relevant_sentences[0]
            if len(description) > 200:
                description = description[:197] + "..."
            return description
        else:
            return "Actionable content identified based on keyword analysis."

    def _extract_theoretical_description(self, content: str, keywords: List[str]) -> str:
        """Extract a description of the theoretical insight."""
        sentences = re.split(r'[.!?]+', content)
        relevant_sentences = []

        for sentence in sentences[:10]:
            sentence = sentence.strip()
            if any(keyword in sentence.lower() for keyword in keywords):
                relevant_sentences.append(sentence)

        if relevant_sentences:
            description = relevant_sentences[0]
            if len(description) > 200:
                description = description[:197] + "..."
            return description
        else:
            return "Theoretical content identified based on conceptual keyword analysis."

    def _extract_related_concepts(self, content: str, tags: List[str]) -> List[str]:
        """Extract related concepts from content and tags."""
        # Use tags as primary source of related concepts
        concepts = list(tags)

        # Add some common technical concepts found in content
        technical_concepts = [
            'machine learning', 'artificial intelligence', 'data science',
            'software engineering', 'devops', 'cloud computing', 'microservices',
            'api design', 'database', 'security', 'performance', 'scalability'
        ]

        for concept in technical_concepts:
            if concept in content.lower() and concept not in concepts:
                concepts.append(concept)

        return concepts[:8]  # Limit to 8 concepts

    def _suggest_research_directions(self, content: str, keywords: List[str]) -> List[str]:
        """Suggest research directions based on content analysis."""
        directions = []

        # Generic research directions based on keywords
        if 'analysis' in keywords or 'study' in keywords:
            directions.append("Conduct deeper quantitative analysis")

        if 'comparison' in keywords or 'evaluation' in keywords:
            directions.append("Perform comparative studies with alternatives")

        if 'future' in keywords or 'trend' in keywords:
            directions.append("Investigate emerging trends and future developments")

        if 'research' in keywords:
            directions.append("Review recent academic literature")

        # Add some default directions if none found
        if not directions:
            directions = [
                "Explore practical applications",
                "Investigate related methodologies",
                "Study implementation case studies"
            ]

        return directions[:5]  # Limit to 5 directions

    def _calculate_content_statistics(self, content_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive statistics about the analyzed content."""
        if not content_list:
            return {}

        total_files = len(content_list)
        total_words = sum(item.get('word_count', 0) for item in content_list)
        total_headings = sum(item.get('heading_count', 0) for item in content_list)

        # Tag statistics
        all_tags = []
        for item in content_list:
            all_tags.extend(item.get('tags', []))

        unique_tags = len(set(all_tags))
        tag_counts = Counter(all_tags)

        # Quality statistics
        quality_scores = [item.get('quality_score', 0.5) for item in content_list]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            'total_files': total_files,
            'total_words': total_words,
            'average_words_per_file': total_words / total_files if total_files > 0 else 0,
            'total_headings': total_headings,
            'average_headings_per_file': total_headings / total_files if total_files > 0 else 0,
            'unique_tags': unique_tags,
            'total_tag_instances': len(all_tags),
            'average_tags_per_file': len(all_tags) / total_files if total_files > 0 else 0,
            'most_common_tags': tag_counts.most_common(10),
            'average_quality_score': avg_quality,
            'high_quality_files': len([s for s in quality_scores if s >= 0.7]),
            'low_quality_files': len([s for s in quality_scores if s < 0.3])
        }

    def _calculate_quality_metrics(self, content_list: List[Dict[str, Any]],
                                 topic_groups: List[TopicGroup]) -> Dict[str, float]:
        """Calculate quality metrics for the analysis."""
        if not content_list:
            return {}

        # Content coverage - how much content is grouped
        grouped_file_ids = set()
        for group in topic_groups:
            for doc in group.documents:
                grouped_file_ids.add(doc['id'])

        coverage = len(grouped_file_ids) / len(content_list) if content_list else 0

        # Group quality - average quality of groups
        group_qualities = [group.content_quality_score for group in topic_groups]
        avg_group_quality = sum(group_qualities) / len(group_qualities) if group_qualities else 0

        # Tag hierarchy depth
        all_tags = []
        for item in content_list:
            all_tags.extend(item.get('tags', []))

        hierarchical_tags = [tag for tag in all_tags if '/' in tag]
        hierarchy_ratio = len(hierarchical_tags) / len(all_tags) if all_tags else 0

        return {
            'content_coverage': coverage,
            'average_group_quality': avg_group_quality,
            'hierarchy_utilization': hierarchy_ratio,
            'analysis_completeness': min(1.0, len(topic_groups) / 5.0)  # Expect ~5 groups for good analysis
        }