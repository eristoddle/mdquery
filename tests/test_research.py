"""
Unit tests for research and synthesis features.

Tests fuzzy text matching, cross-collection querying, source attribution,
and research organization functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from mdquery.database import DatabaseManager, create_database
from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.cache import CacheManager
from mdquery.research import (
    ResearchEngine, ResearchFilter, FuzzyMatch, CrossCollectionResult,
    SourceAttribution
)


class TestResearchEngine:
    """Test cases for ResearchEngine functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample markdown files for testing."""
        files = {}

        # Research paper 1
        files['research1'] = temp_dir / 'research' / 'ai_paper.md'
        files['research1'].parent.mkdir(parents=True, exist_ok=True)
        files['research1'].write_text("""---
title: "Artificial Intelligence in Healthcare"
author: "Dr. Smith"
date: "2024-01-15"
category: "research"
tags: ["AI", "healthcare", "machine learning"]
url: "https://example.com/ai-healthcare"
---

# Artificial Intelligence in Healthcare

Machine learning algorithms are revolutionizing healthcare diagnostics.

> "AI has the potential to transform medical practice" - Dr. Johnson (2023)

The implementation of neural networks in medical imaging has shown remarkable results.

## Key Findings

According to recent studies, AI systems can achieve 95% accuracy in diagnosis.

- Deep learning models
- Computer vision applications
- Natural language processing

[Related work](../notes/ml_notes.md)
""")

        # Research paper 2
        files['research2'] = temp_dir / 'research' / 'ml_algorithms.md'
        files['research2'].write_text("""---
title: "Machine Learning Algorithms Comparison"
author: "Dr. Johnson"
date: "2024-02-01"
category: "research"
tags: ["machine learning", "algorithms", "comparison"]
---

# Machine Learning Algorithms Comparison

This paper compares various machine learning approaches for classification tasks.

## Supervised Learning

Random forests and support vector machines show excellent performance.

> "The choice of algorithm depends on the specific problem domain" - Smith et al. (2024)

### Neural Networks

Deep learning has become the gold standard for many applications.
""")

        # Blog post
        files['blog1'] = temp_dir / 'blog' / 'ai_trends.md'
        files['blog1'].parent.mkdir(parents=True, exist_ok=True)
        files['blog1'].write_text("""---
title: "AI Trends in 2024"
author: "Tech Writer"
date: "2024-03-01"
category: "blog"
tags: ["AI", "trends", "technology"]
---

# AI Trends in 2024

Artificial intelligence continues to evolve rapidly.

The integration of AI in various industries is accelerating.

## Healthcare Applications

Machine learning is making significant impacts in medical diagnosis.
""")

        # Notes file
        files['notes1'] = temp_dir / 'notes' / 'ml_notes.md'
        files['notes1'].parent.mkdir(parents=True, exist_ok=True)
        files['notes1'].write_text("""---
title: "Machine Learning Notes"
author: "Student"
date: "2024-01-20"
category: "notes"
tags: ["machine learning", "study notes"]
---

# Machine Learning Notes

Key concepts in machine learning:

- Supervised learning
- Unsupervised learning
- Reinforcement learning

## Algorithms

Various algorithms exist for different problem types.
""")

        return files

    @pytest.fixture
    def indexed_database(self, temp_dir, sample_files):
        """Create and populate database with sample files."""
        db_path = temp_dir / 'test.db'
        db_manager = create_database(db_path)
        cache_manager = CacheManager(db_path, db_manager)
        indexer = Indexer(db_manager, cache_manager)

        # Index all sample files
        for file_path in sample_files.values():
            indexer.index_file(file_path)

        return db_manager

    @pytest.fixture
    def research_engine(self, indexed_database):
        """Create ResearchEngine instance with indexed data."""
        query_engine = QueryEngine(indexed_database)
        return ResearchEngine(query_engine)

    def test_fuzzy_search_basic(self, research_engine):
        """Test basic fuzzy text matching functionality."""
        # Search for AI-related content
        matches = research_engine.fuzzy_search("artificial intelligence", similarity_threshold=0.3)

        assert len(matches) > 0

        # Check that we found relevant matches
        ai_matches = [m for m in matches if 'artificial' in m.matched_text.lower() or 'ai' in m.matched_text.lower()]
        assert len(ai_matches) > 0

        # Verify match structure
        match = matches[0]
        assert isinstance(match, FuzzyMatch)
        assert match.file_path
        assert match.matched_text
        assert 0.0 <= match.similarity_score <= 1.0
        assert match.match_type in ['content', 'title', 'heading']

    def test_fuzzy_search_threshold(self, research_engine):
        """Test fuzzy search with different similarity thresholds."""
        search_text = "machine learning algorithms"

        # High threshold should return fewer results
        high_threshold_matches = research_engine.fuzzy_search(search_text, similarity_threshold=0.8)
        low_threshold_matches = research_engine.fuzzy_search(search_text, similarity_threshold=0.3)

        assert len(high_threshold_matches) <= len(low_threshold_matches)

        # All high threshold matches should have high similarity
        for match in high_threshold_matches:
            assert match.similarity_score >= 0.8

    def test_fuzzy_search_fields(self, research_engine):
        """Test fuzzy search with specific field restrictions."""
        search_text = "Healthcare"

        # Search only in titles
        title_matches = research_engine.fuzzy_search(search_text, search_fields=['title'])

        # Search only in content
        content_matches = research_engine.fuzzy_search(search_text, search_fields=['content'])

        # Verify field restrictions
        for match in title_matches:
            assert match.match_type == 'title'

        for match in content_matches:
            assert match.match_type == 'content'

    def test_fuzzy_search_max_results(self, research_engine):
        """Test fuzzy search result limiting."""
        matches = research_engine.fuzzy_search("learning", max_results=2)

        assert len(matches) <= 2

    def test_cross_collection_search(self, research_engine):
        """Test cross-collection querying functionality."""
        # Search across research and blog collections
        results = research_engine.cross_collection_search(
            "artificial intelligence",
            ["research", "blog"],
            max_results_per_collection=10
        )

        assert len(results) > 0

        # Verify result structure
        result = results[0]
        assert isinstance(result, CrossCollectionResult)
        assert result.collection_name in ["research", "blog"]
        assert result.file_path
        assert result.relevance_score >= 0.0
        assert isinstance(result.matched_fields, list)
        assert isinstance(result.metadata, dict)

    def test_cross_collection_search_relevance_scoring(self, research_engine):
        """Test relevance scoring in cross-collection search."""
        results = research_engine.cross_collection_search(
            "machine learning",
            ["research", "notes"],
            max_results_per_collection=5
        )

        # Results should be sorted by relevance score (descending)
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score

    def test_extract_quotes_with_attribution(self, research_engine):
        """Test quote extraction with source attribution."""
        attributions = research_engine.extract_quotes_with_attribution()

        assert len(attributions) > 0

        # Verify attribution structure
        attr = attributions[0]
        assert isinstance(attr, SourceAttribution)
        assert attr.source_file
        assert attr.quote_text
        assert attr.citation_format

        # Check for expected quotes from sample files
        quote_texts = [attr.quote_text for attr in attributions]
        ai_quotes = [q for q in quote_texts if 'AI has the potential' in q or 'choice of algorithm' in q]
        assert len(ai_quotes) > 0

    def test_extract_quotes_custom_patterns(self, research_engine):
        """Test quote extraction with custom patterns."""
        # Custom pattern for "According to" phrases
        custom_patterns = [r'According to ([^,]+), (.+)']

        attributions = research_engine.extract_quotes_with_attribution(
            quote_patterns=custom_patterns
        )

        # Should find the "According to recent studies" quote
        according_quotes = [attr for attr in attributions if 'According to' in attr.quote_text]
        assert len(according_quotes) > 0

    def test_extract_quotes_specific_files(self, research_engine, sample_files):
        """Test quote extraction from specific files."""
        # Extract quotes only from research files
        research_files = [str(sample_files['research1'])]

        attributions = research_engine.extract_quotes_with_attribution(file_paths=research_files)

        # All attributions should be from the specified file
        for attr in attributions:
            assert attr.source_file in research_files

    def test_filter_by_research_criteria_dates(self, research_engine):
        """Test filtering by date ranges."""
        # Filter for content from January 2024
        date_filter = ResearchFilter(
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 1, 31)
        )

        result = research_engine.filter_by_research_criteria(date_filter)

        assert result.row_count > 0

        # Check that results are within date range
        for row in result.rows:
            modified_date = datetime.fromisoformat(row['modified_date'].replace('Z', '+00:00').replace('+00:00', ''))
            assert datetime(2024, 1, 1) <= modified_date <= datetime(2024, 1, 31)

    def test_filter_by_research_criteria_topics(self, research_engine):
        """Test filtering by topics/tags."""
        # Filter for AI-related content
        topic_filter = ResearchFilter(topics=["AI", "machine learning"])

        result = research_engine.filter_by_research_criteria(topic_filter)

        assert result.row_count > 0

        # Check that results contain relevant tags
        for row in result.rows:
            tags = row.get('tags', '') or ''
            assert any(topic.lower() in tags.lower() for topic in ["AI", "machine learning"])

    def test_filter_by_research_criteria_authors(self, research_engine):
        """Test filtering by authors."""
        # Filter for Dr. Smith's work
        author_filter = ResearchFilter(authors=["Dr. Smith"])

        result = research_engine.filter_by_research_criteria(author_filter)

        assert result.row_count > 0

        # Check that results are by the specified author
        for row in result.rows:
            assert row.get('author') == "Dr. Smith"

    def test_filter_by_research_criteria_collections(self, research_engine):
        """Test filtering by collections/directories."""
        # Filter for research collection
        collection_filter = ResearchFilter(collections=["research"])

        result = research_engine.filter_by_research_criteria(collection_filter)

        assert result.row_count > 0

        # Check that results are from research directory
        for row in result.rows:
            assert 'research' in row['directory']

    def test_filter_by_research_criteria_combined(self, research_engine):
        """Test filtering with multiple criteria."""
        # Combine multiple filters
        combined_filter = ResearchFilter(
            topics=["machine learning"],
            authors=["Dr. Johnson"],
            date_from=datetime(2024, 2, 1)
        )

        result = research_engine.filter_by_research_criteria(combined_filter)

        # Should find Dr. Johnson's ML paper from February
        assert result.row_count > 0

    def test_generate_research_summary_basic(self, research_engine):
        """Test basic research summary generation."""
        summary = research_engine.generate_research_summary()

        # Check summary structure
        assert 'basic_stats' in summary
        assert 'source_distribution' in summary
        assert 'topic_analysis' in summary
        assert 'temporal_patterns' in summary
        assert 'author_productivity' in summary

        # Check basic stats
        basic_stats = summary['basic_stats']
        assert basic_stats['total_files'] > 0
        assert basic_stats['total_words'] > 0

    def test_generate_research_summary_filtered(self, research_engine):
        """Test research summary with filtering."""
        # Generate summary for research collection only
        research_filter = ResearchFilter(collections=["research"])

        summary = research_engine.generate_research_summary(research_filter)

        # Should have fewer files than total
        basic_stats = summary['basic_stats']
        assert basic_stats['total_files'] > 0

        # Source distribution should only show research
        source_dist = summary['source_distribution']
        for source in source_dist:
            assert 'research' in source['collection']

    def test_generate_research_summary_topic_analysis(self, research_engine):
        """Test topic analysis in research summary."""
        summary = research_engine.generate_research_summary()

        topic_analysis = summary['topic_analysis']
        assert len(topic_analysis) > 0

        # Should find common topics like AI, machine learning
        topics = [item['topic'] for item in topic_analysis]
        ai_topics = [t for t in topics if 'AI' in t or 'machine learning' in t]
        assert len(ai_topics) > 0

    def test_generate_research_summary_author_productivity(self, research_engine):
        """Test author productivity analysis."""
        summary = research_engine.generate_research_summary()

        author_productivity = summary['author_productivity']
        assert len(author_productivity) > 0

        # Should find authors from sample data
        authors = [item['author'] for item in author_productivity]
        expected_authors = ['Dr. Smith', 'Dr. Johnson']
        found_authors = [a for a in authors if a in expected_authors]
        assert len(found_authors) > 0

    def test_research_filter_dataclass(self):
        """Test ResearchFilter dataclass functionality."""
        # Test with all parameters
        filter_obj = ResearchFilter(
            date_from=datetime(2024, 1, 1),
            date_to=datetime(2024, 12, 31),
            topics=["AI", "ML"],
            sources=["research", "papers"],
            authors=["Dr. Smith"],
            collections=["research"]
        )

        assert filter_obj.date_from == datetime(2024, 1, 1)
        assert filter_obj.topics == ["AI", "ML"]
        assert filter_obj.authors == ["Dr. Smith"]

        # Test with no parameters (all None)
        empty_filter = ResearchFilter()
        assert empty_filter.date_from is None
        assert empty_filter.topics is None

    def test_fuzzy_match_dataclass(self):
        """Test FuzzyMatch dataclass functionality."""
        match = FuzzyMatch(
            file_path="/test/file.md",
            matched_text="test content",
            similarity_score=0.85,
            context_before="before",
            context_after="after",
            match_type="content",
            line_number=42
        )

        assert match.file_path == "/test/file.md"
        assert match.similarity_score == 0.85
        assert match.match_type == "content"
        assert match.line_number == 42

    def test_cross_collection_result_dataclass(self):
        """Test CrossCollectionResult dataclass functionality."""
        result = CrossCollectionResult(
            collection_name="research",
            file_path="/test/file.md",
            relevance_score=0.92,
            matched_fields=["title", "content"],
            metadata={"author": "Dr. Smith"}
        )

        assert result.collection_name == "research"
        assert result.relevance_score == 0.92
        assert result.matched_fields == ["title", "content"]
        assert result.metadata["author"] == "Dr. Smith"

    def test_source_attribution_dataclass(self):
        """Test SourceAttribution dataclass functionality."""
        attribution = SourceAttribution(
            source_file="/test/file.md",
            quote_text="This is a quote",
            context="surrounding context",
            author="Dr. Smith",
            title="Test Paper",
            date="2024-01-01",
            page_number="42",
            url="https://example.com",
            citation_format="Smith (2024). Test Paper."
        )

        assert attribution.source_file == "/test/file.md"
        assert attribution.quote_text == "This is a quote"
        assert attribution.author == "Dr. Smith"
        assert attribution.citation_format == "Smith (2024). Test Paper."

    def test_fuzzy_search_empty_query(self, research_engine):
        """Test fuzzy search with empty query."""
        matches = research_engine.fuzzy_search("", similarity_threshold=0.5)
        assert len(matches) == 0

    def test_fuzzy_search_no_matches(self, research_engine):
        """Test fuzzy search with query that has no matches."""
        matches = research_engine.fuzzy_search("xyzzyx nonexistent content", similarity_threshold=0.5)
        assert len(matches) == 0

    def test_cross_collection_search_empty_collections(self, research_engine):
        """Test cross-collection search with empty collections list."""
        results = research_engine.cross_collection_search("test", [])
        assert len(results) == 0

    def test_cross_collection_search_nonexistent_collection(self, research_engine):
        """Test cross-collection search with nonexistent collection."""
        results = research_engine.cross_collection_search("test", ["nonexistent"])
        assert len(results) == 0

    def test_extract_quotes_no_files(self, research_engine):
        """Test quote extraction with empty file list."""
        attributions = research_engine.extract_quotes_with_attribution(file_paths=[])
        assert len(attributions) == 0

    def test_filter_by_research_criteria_no_results(self, research_engine):
        """Test research filtering with criteria that match no files."""
        # Filter for future dates
        future_filter = ResearchFilter(
            date_from=datetime(2025, 1, 1),
            date_to=datetime(2025, 12, 31)
        )

        result = research_engine.filter_by_research_criteria(future_filter)
        assert result.row_count == 0

    @patch('mdquery.research.difflib.SequenceMatcher')
    def test_fuzzy_search_algorithm_error_handling(self, mock_matcher, research_engine):
        """Test fuzzy search error handling in similarity algorithms."""
        # Mock SequenceMatcher to raise an exception
        mock_matcher.side_effect = Exception("Algorithm error")

        # Should handle the error gracefully and return empty results
        matches = research_engine.fuzzy_search("test query")
        assert isinstance(matches, list)

    def test_research_engine_initialization(self, indexed_database):
        """Test ResearchEngine initialization."""
        query_engine = QueryEngine(indexed_database)
        research_engine = ResearchEngine(query_engine)

        assert research_engine.query_engine == query_engine
        assert research_engine.db_manager == query_engine.db_manager

    def test_normalize_text_method(self, research_engine):
        """Test text normalization functionality."""
        # Test with markdown formatting
        text = "This is **bold** and *italic* text with `code`"
        normalized = research_engine._normalize_text(text)

        # Should remove markdown formatting
        assert "**" not in normalized
        assert "*" not in normalized
        assert "`" not in normalized
        assert "bold" in normalized
        assert "italic" in normalized

    def test_word_overlap_similarity(self, research_engine):
        """Test word overlap similarity calculation."""
        text1 = "machine learning algorithms"
        text2 = "algorithms for machine learning"

        similarity = research_engine._calculate_word_overlap_similarity(text1, text2)

        # Should have high similarity due to word overlap
        assert similarity > 0.5

    def test_citation_generation(self, research_engine):
        """Test citation format generation."""
        metadata = {
            'author': 'Dr. Smith',
            'title': 'Test Paper',
            'date': '2024-01-01',
            'url': 'https://example.com'
        }

        citation = research_engine._generate_citation('/test/file.md', metadata, 'test quote')

        assert 'Dr. Smith' in citation
        assert '2024-01-01' in citation
        assert 'Test Paper' in citation
        assert 'https://example.com' in citation


class TestResearchIntegration:
    """Integration tests for research features."""

    @pytest.fixture
    def temp_research_project(self):
        """Create a temporary research project structure."""
        temp_dir = tempfile.mkdtemp()
        project_dir = Path(temp_dir)

        # Create research project structure
        (project_dir / 'papers').mkdir()
        (project_dir / 'notes').mkdir()
        (project_dir / 'drafts').mkdir()

        # Create sample research files
        (project_dir / 'papers' / 'ai_survey.md').write_text("""---
title: "AI Survey 2024"
author: "Research Team"
date: "2024-01-15"
category: "survey"
tags: ["AI", "survey", "2024"]
---

# Artificial Intelligence Survey 2024

This comprehensive survey covers recent advances in AI.

> "The field of AI is rapidly evolving" - Expert Panel (2024)

## Machine Learning Trends

Deep learning continues to dominate the landscape.
""")

        (project_dir / 'notes' / 'meeting_notes.md').write_text("""---
title: "Research Meeting Notes"
author: "Assistant"
date: "2024-02-01"
category: "notes"
tags: ["meeting", "research", "planning"]
---

# Research Meeting Notes

Discussion points from today's research meeting.

## Action Items

- Review AI survey paper
- Prepare presentation slides
- Schedule follow-up meeting
""")

        yield project_dir
        shutil.rmtree(temp_dir)

    def test_end_to_end_research_workflow(self, temp_research_project):
        """Test complete research workflow from indexing to analysis."""
        # Set up database and indexing
        db_path = temp_research_project / 'research.db'
        db_manager = create_database(db_path)
        cache_manager = CacheManager(db_path, db_manager)
        indexer = Indexer(db_manager, cache_manager)

        # Index the research project
        indexer.index_directory(temp_research_project, recursive=True)

        # Create research engine
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Test fuzzy search
        ai_matches = research_engine.fuzzy_search("artificial intelligence")
        assert len(ai_matches) > 0

        # Test cross-collection search
        cross_results = research_engine.cross_collection_search(
            "research", ["papers", "notes"]
        )
        assert len(cross_results) > 0

        # Test quote extraction
        quotes = research_engine.extract_quotes_with_attribution()
        assert len(quotes) > 0

        # Test research filtering
        research_filter = ResearchFilter(
            topics=["AI"],
            date_from=datetime(2024, 1, 1)
        )
        filtered_results = research_engine.filter_by_research_criteria(research_filter)
        assert filtered_results.row_count > 0

        # Test research summary
        summary = research_engine.generate_research_summary()
        assert summary['basic_stats']['total_files'] > 0

        # Cleanup
        db_manager.close()

    def test_research_performance_with_large_dataset(self, temp_research_project):
        """Test research features performance with larger dataset."""
        # Create more files for performance testing
        for i in range(20):
            file_path = temp_research_project / f'generated_{i}.md'
            file_path.write_text(f"""---
title: "Generated Paper {i}"
author: "Generator"
date: "2024-01-{i+1:02d}"
tags: ["generated", "test", "paper{i}"]
---

# Generated Paper {i}

This is generated content for testing purposes.

Machine learning and artificial intelligence are important topics.

> "Generated quote number {i}" - Author {i}

## Section {i}

Content with various keywords for testing fuzzy matching.
""")

        # Set up and index
        db_path = temp_research_project / 'large_research.db'
        db_manager = create_database(db_path)
        cache_manager = CacheManager(db_path, db_manager)
        indexer = Indexer(db_manager, cache_manager)
        indexer.index_directory(temp_research_project, recursive=True)

        # Create research engine
        query_engine = QueryEngine(db_manager)
        research_engine = ResearchEngine(query_engine)

        # Test performance of various operations
        import time

        # Fuzzy search performance
        start_time = time.time()
        matches = research_engine.fuzzy_search("machine learning", max_results=10)
        fuzzy_time = time.time() - start_time

        assert len(matches) > 0
        assert fuzzy_time < 5.0  # Should complete within 5 seconds

        # Cross-collection search performance
        start_time = time.time()
        cross_results = research_engine.cross_collection_search(
            "artificial intelligence", [str(temp_research_project)]
        )
        cross_time = time.time() - start_time

        assert len(cross_results) > 0
        assert cross_time < 5.0  # Should complete within 5 seconds

        # Research summary performance
        start_time = time.time()
        summary = research_engine.generate_research_summary()
        summary_time = time.time() - start_time

        assert summary['basic_stats']['total_files'] > 20
        assert summary_time < 10.0  # Should complete within 10 seconds

        # Cleanup
        db_manager.close()


if __name__ == '__main__':
    pytest.main([__file__])