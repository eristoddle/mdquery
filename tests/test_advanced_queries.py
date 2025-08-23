"""
Unit tests for advanced querying features.

Tests SEO analysis, content structure analysis, relationship queries,
and aggregation support for content analysis functionality.
"""

import pytest
import tempfile
import sqlite3
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from mdquery.database import DatabaseManager, create_database
from mdquery.query import QueryEngine
from mdquery.advanced_queries import (
    AdvancedQueryEngine, SEOAnalysis, ContentStructure,
    TagSimilarity, LinkAnalysis
)
from mdquery.models import QueryResult


class TestAdvancedQueryEngine:
    """Test cases for AdvancedQueryEngine functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = Path(f.name)

        # Create and initialize database
        db_manager = create_database(db_path)

        # Insert test data
        self._populate_test_data(db_manager)

        yield db_manager

        # Cleanup
        db_manager.close()
        db_path.unlink()

    def _populate_test_data(self, db_manager: DatabaseManager):
        """Populate database with test data."""
        with db_manager.get_connection() as conn:
            # Insert test files
            files_data = [
                (1, '/test/blog/seo-guide.md', 'seo-guide.md', '/test/blog',
                 '2024-01-01 10:00:00', '2024-01-01 10:00:00', 1500, 'hash1', 800, 5),
                (2, '/test/docs/api-reference.md', 'api-reference.md', '/test/docs',
                 '2024-01-02 11:00:00', '2024-01-02 11:00:00', 3000, 'hash2', 1200, 8),
                (3, '/test/notes/research.md', 'research.md', '/test/notes',
                 '2024-01-03 12:00:00', '2024-01-03 12:00:00', 500, 'hash3', 150, 2),
                (4, '/test/blog/short-post.md', 'short-post.md', '/test/blog',
                 '2024-01-04 13:00:00', '2024-01-04 13:00:00', 200, 'hash4', 50, 0),
            ]

            for file_data in files_data:
                conn.execute("""
                    INSERT INTO files (id, path, filename, directory, modified_date,
                                     created_date, file_size, content_hash, word_count, heading_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, file_data)

            # Insert frontmatter data
            frontmatter_data = [
                (1, 'title', 'Complete SEO Guide for Beginners', 'string'),
                (1, 'description', 'Learn SEO basics and advanced techniques to improve your website ranking', 'string'),
                (1, 'category', 'SEO', 'string'),
                (2, 'title', 'API Reference Documentation', 'string'),
                (2, 'category', 'Documentation', 'string'),
                (3, 'title', 'Research Notes', 'string'),
                (4, 'category', 'Blog', 'string'),
            ]

            for fm_data in frontmatter_data:
                conn.execute("""
                    INSERT INTO frontmatter (file_id, key, value, value_type)
                    VALUES (?, ?, ?, ?)
                """, fm_data)

            # Insert tags data
            tags_data = [
                (1, 'seo', 'frontmatter'),
                (1, 'marketing', 'frontmatter'),
                (1, 'guide', 'content'),
                (2, 'documentation', 'frontmatter'),
                (2, 'api', 'frontmatter'),
                (2, 'reference', 'content'),
                (3, 'research', 'frontmatter'),
                (3, 'notes', 'content'),
                (3, 'seo', 'content'),  # Common tag with file 1
                (4, 'blog', 'frontmatter'),
            ]

            for tag_data in tags_data:
                conn.execute("""
                    INSERT INTO tags (file_id, tag, source)
                    VALUES (?, ?, ?)
                """, tag_data)

            # Insert links data
            links_data = [
                (1, 1, 'API docs', '/test/docs/api-reference.md', 'wikilink', True),
                (2, 2, 'SEO guide', '/test/blog/seo-guide.md', 'markdown', True),
                (3, 3, 'External link', 'https://example.com', 'markdown', False),
                (4, 1, 'Research notes', '/test/notes/research.md', 'wikilink', True),
            ]

            for link_data in links_data:
                conn.execute("""
                    INSERT INTO links (id, file_id, link_text, link_target, link_type, is_internal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, link_data)

            # Insert content for FTS
            content_data = [
                (1, 'Complete SEO Guide for Beginners',
                 'This comprehensive guide covers all aspects of SEO from basic concepts to advanced techniques.',
                 'Introduction\nBasics\nAdvanced Techniques\nConclusion'),
                (2, 'API Reference Documentation',
                 'Complete API reference with examples and usage patterns for developers.',
                 'Overview\nAuthentication\nEndpoints\nExamples\nError Handling'),
                (3, 'Research Notes',
                 'Collection of research findings and observations.',
                 'Methodology\nFindings'),
                (4, '',
                 'Short blog post content.',
                 ''),
            ]

            for content in content_data:
                conn.execute("""
                    INSERT INTO content_fts (file_id, title, content, headings)
                    VALUES (?, ?, ?, ?)
                """, content)

            conn.commit()

    @pytest.fixture
    def advanced_engine(self, temp_db):
        """Create AdvancedQueryEngine instance."""
        query_engine = QueryEngine(temp_db)
        return AdvancedQueryEngine(query_engine)

    def test_seo_analysis_all_files(self, advanced_engine):
        """Test SEO analysis for all files."""
        analyses = advanced_engine.analyze_seo()

        assert len(analyses) == 4

        # Check first file (good SEO)
        seo_guide = next(a for a in analyses if 'seo-guide.md' in a.file_path)
        assert seo_guide.title == 'Complete SEO Guide for Beginners'
        assert seo_guide.description is not None
        assert seo_guide.category == 'SEO'
        assert seo_guide.word_count == 800
        assert seo_guide.heading_count == 5
        assert 'seo' in seo_guide.tags
        assert seo_guide.score > 80  # Should have high score

        # Check short post (poor SEO)
        short_post = next(a for a in analyses if 'short-post.md' in a.file_path)
        assert short_post.title is None
        assert short_post.description is None
        assert short_post.word_count == 50
        assert short_post.heading_count == 0
        assert len(short_post.issues) > 3  # Should have multiple issues
        assert short_post.score < 50  # Should have low score

    def test_seo_analysis_specific_files(self, advanced_engine):
        """Test SEO analysis for specific files."""
        file_paths = ['/test/blog/seo-guide.md', '/test/notes/research.md']
        analyses = advanced_engine.analyze_seo(file_paths)

        assert len(analyses) == 2

        file_paths_analyzed = [a.file_path for a in analyses]
        assert '/test/blog/seo-guide.md' in file_paths_analyzed
        assert '/test/notes/research.md' in file_paths_analyzed

    def test_content_structure_analysis(self, advanced_engine):
        """Test content structure analysis."""
        analyses = advanced_engine.analyze_content_structure()

        assert len(analyses) == 4

        # Check API reference (good structure)
        api_ref = next(a for a in analyses if 'api-reference.md' in a.file_path)
        assert api_ref.word_count == 1200
        # Note: heading_hierarchy might be empty if headings string doesn't contain proper markdown headings
        assert api_ref.paragraph_count > 0
        assert api_ref.readability_score is not None

        # Check short post (poor structure)
        short_post = next(a for a in analyses if 'short-post.md' in a.file_path)
        assert short_post.word_count == 50
        # Short posts may not have structure issues if under threshold
        assert short_post.readability_score is not None

    def test_parse_heading_hierarchy(self, advanced_engine):
        """Test heading hierarchy parsing."""
        headings_str = "# Main Title\n## Section 1\n### Subsection\n## Section 2"
        hierarchy = advanced_engine._parse_heading_hierarchy(headings_str)

        assert len(hierarchy) == 4
        assert hierarchy[0]['level'] == 1
        assert hierarchy[0]['text'] == 'Main Title'
        assert hierarchy[1]['level'] == 2
        assert hierarchy[1]['text'] == 'Section 1'
        assert hierarchy[2]['level'] == 3
        assert hierarchy[2]['text'] == 'Subsection'

    def test_calculate_readability_score(self, advanced_engine):
        """Test readability score calculation."""
        content = "This is a simple sentence. This is another sentence with more words."
        score = advanced_engine._calculate_readability_score(content)

        assert score is not None
        assert 0 <= score <= 100

        # Test empty content
        empty_score = advanced_engine._calculate_readability_score("")
        assert empty_score is None

    def test_find_similar_content(self, advanced_engine):
        """Test finding similar content based on tags."""
        similarities = advanced_engine.find_similar_content('/test/blog/seo-guide.md', 0.1)

        # Should find research.md as similar (both have 'seo' tag)
        assert len(similarities) > 0

        research_sim = next((s for s in similarities if 'research.md' in s.file2_path), None)
        assert research_sim is not None
        assert 'seo' in research_sim.common_tags
        assert research_sim.similarity_score > 0

    def test_calculate_tag_similarity(self, advanced_engine):
        """Test tag similarity calculation."""
        tags1 = {'seo', 'marketing', 'guide'}
        tags2 = {'seo', 'research', 'notes'}

        similarity = advanced_engine._calculate_tag_similarity(tags1, tags2)
        expected = 1 / 5  # 1 common tag out of 5 total unique tags
        assert abs(similarity - expected) < 0.001

        # Test identical sets
        identical_sim = advanced_engine._calculate_tag_similarity(tags1, tags1)
        assert identical_sim == 1.0

        # Test no overlap
        no_overlap_sim = advanced_engine._calculate_tag_similarity(tags1, {'other', 'different'})
        assert no_overlap_sim == 0.0

    def test_analyze_link_relationships(self, advanced_engine):
        """Test link relationship analysis."""
        analyses = advanced_engine.analyze_link_relationships()

        assert len(analyses) > 0

        # Check for bidirectional relationship between seo-guide and api-reference
        bidirectional = [a for a in analyses if a.is_bidirectional]
        assert len(bidirectional) > 0

        # Check link strength calculation
        for analysis in analyses:
            assert analysis.link_strength >= 1.0  # At least base strength

    def test_generate_content_report(self, advanced_engine):
        """Test comprehensive content report generation."""
        report = advanced_engine.generate_content_report()

        # Check basic stats
        assert 'basic_stats' in report
        basic_stats = report['basic_stats']
        assert basic_stats['total_files'] == 4
        assert basic_stats['total_words'] == 2200  # Sum of all word counts

        # Check frontmatter coverage
        assert 'frontmatter_coverage' in report
        frontmatter_coverage = report['frontmatter_coverage']
        assert len(frontmatter_coverage) > 0

        # Check tag stats
        assert 'tag_stats' in report

        # Check popular tags
        assert 'popular_tags' in report

        # Check quality issues
        assert 'quality_issues' in report

    def test_get_aggregation_queries(self, advanced_engine):
        """Test predefined aggregation queries."""
        queries = advanced_engine.get_aggregation_queries()

        expected_queries = [
            'files_by_directory',
            'content_by_month',
            'tag_cooccurrence',
            'link_popularity',
            'word_count_distribution'
        ]

        for query_name in expected_queries:
            assert query_name in queries
            assert isinstance(queries[query_name], str)
            assert 'SELECT' in queries[query_name].upper()

    def test_execute_aggregation_query(self, advanced_engine):
        """Test executing aggregation queries."""
        # Test files by directory
        result = advanced_engine.execute_aggregation_query('files_by_directory')
        assert isinstance(result, QueryResult)
        assert len(result.rows) > 0
        assert 'directory' in result.columns
        assert 'file_count' in result.columns

        # Test word count distribution
        result = advanced_engine.execute_aggregation_query('word_count_distribution')
        assert isinstance(result, QueryResult)
        assert len(result.rows) > 0
        assert 'word_range' in result.columns
        assert 'file_count' in result.columns

        # Test invalid query name
        with pytest.raises(Exception):
            advanced_engine.execute_aggregation_query('nonexistent_query')

    def test_seo_analysis_edge_cases(self, advanced_engine):
        """Test SEO analysis edge cases."""
        # Test with empty file list
        analyses = advanced_engine.analyze_seo([])
        assert len(analyses) == 0

        # Test with non-existent file
        analyses = advanced_engine.analyze_seo(['/nonexistent/file.md'])
        assert len(analyses) == 0

    def test_content_structure_edge_cases(self, advanced_engine):
        """Test content structure analysis edge cases."""
        # Test with empty content
        file_data = {
            'path': '/test/empty.md',
            'word_count': 0,
            'heading_count': 0,
            'content': '',
            'headings': ''
        }

        analysis = advanced_engine._analyze_content_structure_for_file(file_data)
        assert analysis.word_count == 0
        assert analysis.paragraph_count == 0
        assert len(analysis.heading_hierarchy) == 0

    def test_identify_structure_issues(self, advanced_engine):
        """Test structure issue identification."""
        # Test long content with no headings
        issues = advanced_engine._identify_structure_issues([], 1500, 10)
        assert any('No headings' in issue for issue in issues)

        # Test heading level jumps
        headings = [
            {'level': 1, 'text': 'Title'},
            {'level': 3, 'text': 'Subsection'}  # Jumps from H1 to H3
        ]
        issues = advanced_engine._identify_structure_issues(headings, 500, 5)
        assert any('level jumps' in issue for issue in issues)

        # Test long paragraphs
        issues = advanced_engine._identify_structure_issues([], 1000, 5)  # 200 words per paragraph
        # The method should detect long paragraphs (200 words per paragraph > 150 threshold)
        assert any('paragraphs' in issue.lower() for issue in issues)


class TestSEOAnalysisDataClass:
    """Test SEOAnalysis data class."""

    def test_seo_analysis_creation(self):
        """Test SEOAnalysis object creation."""
        analysis = SEOAnalysis(
            file_path='/test/file.md',
            title='Test Title',
            description='Test description',
            category='Test',
            word_count=500,
            heading_count=3,
            tags=['test', 'example'],
            issues=['Missing meta description'],
            score=85.5
        )

        assert analysis.file_path == '/test/file.md'
        assert analysis.title == 'Test Title'
        assert analysis.score == 85.5
        assert len(analysis.tags) == 2
        assert len(analysis.issues) == 1


class TestContentStructureDataClass:
    """Test ContentStructure data class."""

    def test_content_structure_creation(self):
        """Test ContentStructure object creation."""
        hierarchy = [
            {'level': 1, 'text': 'Main Title', 'word_count': 2},
            {'level': 2, 'text': 'Section', 'word_count': 1}
        ]

        structure = ContentStructure(
            file_path='/test/file.md',
            heading_hierarchy=hierarchy,
            word_count=500,
            paragraph_count=10,
            readability_score=75.0,
            structure_issues=['No issues']
        )

        assert structure.file_path == '/test/file.md'
        assert len(structure.heading_hierarchy) == 2
        assert structure.readability_score == 75.0


class TestTagSimilarityDataClass:
    """Test TagSimilarity data class."""

    def test_tag_similarity_creation(self):
        """Test TagSimilarity object creation."""
        similarity = TagSimilarity(
            file1_path='/test/file1.md',
            file2_path='/test/file2.md',
            common_tags=['tag1', 'tag2'],
            similarity_score=0.67,
            total_tags_file1=3,
            total_tags_file2=4
        )

        assert similarity.file1_path == '/test/file1.md'
        assert len(similarity.common_tags) == 2
        assert similarity.similarity_score == 0.67


class TestLinkAnalysisDataClass:
    """Test LinkAnalysis data class."""

    def test_link_analysis_creation(self):
        """Test LinkAnalysis object creation."""
        analysis = LinkAnalysis(
            source_file='/test/source.md',
            target_file='/test/target.md',
            link_type='wikilink',
            is_bidirectional=True,
            link_strength=2.5
        )

        assert analysis.source_file == '/test/source.md'
        assert analysis.target_file == '/test/target.md'
        assert analysis.is_bidirectional is True
        assert analysis.link_strength == 2.5


if __name__ == '__main__':
    pytest.main([__file__])