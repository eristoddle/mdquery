"""
Tests for comprehensive tag analysis functionality.

This module tests the TagAnalysisEngine and its integration with the MCP server,
verifying hierarchical tag support, content grouping, insight extraction,
and quality filtering capabilities.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from mdquery.tag_analysis import TagAnalysisEngine, TagAnalysisResult, TopicGroup, ActionableInsight, TheoreticalInsight
from mdquery.query import QueryEngine
from mdquery.database import DatabaseManager
from mdquery.models import QueryResult


class TestTagAnalysisEngine:
    """Test cases for TagAnalysisEngine."""

    @pytest.fixture
    def mock_query_engine(self):
        """Create a mock query engine for testing."""
        mock_engine = Mock(spec=QueryEngine)
        mock_db_manager = Mock(spec=DatabaseManager)
        mock_engine.db_manager = mock_db_manager
        return mock_engine

    @pytest.fixture
    def tag_analysis_engine(self, mock_query_engine):
        """Create TagAnalysisEngine instance for testing."""
        return TagAnalysisEngine(mock_query_engine)

    @pytest.fixture
    def sample_content_data(self):
        """Sample content data for testing."""
        return [
            {
                'id': 1,
                'path': '/notes/ai-development.md',
                'word_count': 500,
                'heading_count': 3,
                'created_date': '2024-01-01T10:00:00Z',
                'modified_date': '2024-01-15T14:30:00Z',
                'content': 'This is a guide on implementing AI agents using modern frameworks. The process involves setting up the development environment, configuring the agent architecture, and testing the implementation.',
                'headings': '# AI Agent Development\n## Setup Process\n## Implementation Guide',
                'tags': ['ai', 'agents', 'development', 'implementation'],
                'title': 'AI Agent Development Guide',
                'description': 'Comprehensive guide for building AI agents',
                'category': 'tutorial'
            },
            {
                'id': 2,
                'path': '/notes/llm-theory.md',
                'word_count': 800,
                'heading_count': 4,
                'created_date': '2024-01-02T09:00:00Z',
                'modified_date': '2024-01-16T11:20:00Z',
                'content': 'This document explores the theoretical foundations of large language models. It discusses the underlying principles, research directions, and future possibilities in the field.',
                'headings': '# LLM Theory\n## Foundations\n## Research Areas\n## Future Directions',
                'tags': ['llm', 'theory', 'research', 'ai'],
                'title': 'Large Language Model Theory',
                'description': 'Theoretical exploration of LLM concepts',
                'category': 'research'
            },
            {
                'id': 3,
                'path': '/notes/quick-note.md',
                'word_count': 50,
                'heading_count': 0,
                'created_date': '2024-01-03T16:00:00Z',
                'modified_date': '2024-01-03T16:05:00Z',
                'content': 'Just a quick reminder to check the API documentation later.',
                'headings': '',
                'tags': ['reminder', 'todo'],
                'title': 'Quick Note',
                'description': None,
                'category': None
            }
        ]

    def test_calculate_content_quality_score(self, tag_analysis_engine, sample_content_data):
        """Test content quality score calculation."""
        # High quality content
        high_quality = sample_content_data[0]
        score = tag_analysis_engine._calculate_content_quality_score(high_quality)
        assert score > 0.7, f"Expected high quality score, got {score}"

        # Low quality content (short, no structure)
        low_quality = sample_content_data[2]
        score = tag_analysis_engine._calculate_content_quality_score(low_quality)
        assert score < 0.5, f"Expected low quality score, got {score}"

    def test_filter_content_quality(self, tag_analysis_engine, sample_content_data):
        """Test content quality filtering."""
        # Filter with moderate threshold
        filtered = tag_analysis_engine._filter_content_quality(sample_content_data, 0.5)

        # Should filter out the low-quality quick note
        assert len(filtered) < len(sample_content_data)
        assert all(item.get('quality_score', 0) >= 0.5 for item in filtered)

    def test_build_tag_hierarchy(self, tag_analysis_engine):
        """Test hierarchical tag structure building."""
        content_with_hierarchical_tags = [
            {
                'id': 1,
                'tags': ['ai/agents', 'ai/llm', 'development/tools', 'development/process']
            },
            {
                'id': 2,
                'tags': ['ai/research', 'theory', 'ai/applications']
            }
        ]

        hierarchy = tag_analysis_engine._build_tag_hierarchy(content_with_hierarchical_tags)

        # Check that hierarchical relationships are built
        assert 'ai' in hierarchy
        assert 'ai/agents' in hierarchy['ai']
        assert 'ai/llm' in hierarchy['ai']
        assert 'development' in hierarchy
        assert 'development/tools' in hierarchy['development']

    def test_group_by_semantic_similarity(self, tag_analysis_engine, sample_content_data):
        """Test semantic similarity grouping."""
        # Add quality scores to sample data
        for item in sample_content_data:
            item['quality_score'] = tag_analysis_engine._calculate_content_quality_score(item)

        groups = tag_analysis_engine._group_by_semantic_similarity(sample_content_data)

        # Should create meaningful groups
        assert len(groups) > 0
        assert all(isinstance(group, TopicGroup) for group in groups)
        assert all(len(group.documents) > 0 for group in groups)

    def test_extract_actionable_insights(self, tag_analysis_engine, sample_content_data):
        """Test actionable insight extraction."""
        # Add quality scores
        for item in sample_content_data:
            item['quality_score'] = tag_analysis_engine._calculate_content_quality_score(item)

        insights = tag_analysis_engine._extract_actionable_insights(sample_content_data, [])

        # Should find actionable content (implementation guide)
        actionable_insights = [i for i in insights if 'implementation' in i.description.lower() or 'guide' in i.description.lower()]
        assert len(actionable_insights) > 0

        # Check insight structure
        for insight in insights:
            assert isinstance(insight, ActionableInsight)
            assert insight.implementation_difficulty in ['low', 'medium', 'high']
            assert insight.expected_impact in ['low', 'medium', 'high']
            assert insight.category in ['process', 'tools', 'automation', 'quality']

    def test_extract_theoretical_insights(self, tag_analysis_engine, sample_content_data):
        """Test theoretical insight extraction."""
        # Add quality scores
        for item in sample_content_data:
            item['quality_score'] = tag_analysis_engine._calculate_content_quality_score(item)

        insights = tag_analysis_engine._extract_theoretical_insights(sample_content_data, [])

        # Should find theoretical content
        theoretical_insights = [i for i in insights if 'theory' in i.description.lower() or 'research' in i.description.lower()]
        assert len(theoretical_insights) > 0

        # Check insight structure
        for insight in insights:
            assert isinstance(insight, TheoreticalInsight)
            assert isinstance(insight.related_concepts, list)
            assert isinstance(insight.research_directions, list)

    def test_comprehensive_tag_analysis_integration(self, tag_analysis_engine, mock_query_engine, sample_content_data):
        """Test the complete comprehensive tag analysis workflow."""
        # Mock the query engine to return sample data
        mock_result = Mock(spec=QueryResult)
        mock_result.rows = [
            {
                'id': item['id'],
                'path': item['path'],
                'word_count': item['word_count'],
                'heading_count': item['heading_count'],
                'created_date': item['created_date'],
                'modified_date': item['modified_date'],
                'content': item['content'],
                'headings': item['headings'],
                'all_tags': ','.join(item['tags']),
                'title': item['title'],
                'description': item['description'],
                'category': item['category']
            }
            for item in sample_content_data
        ]

        mock_query_engine.execute_query.return_value = mock_result

        # Run comprehensive analysis
        result = tag_analysis_engine.comprehensive_tag_analysis(
            tag_patterns=['ai', 'development'],
            grouping_strategy='semantic',
            include_actionable=True,
            include_theoretical=True,
            remove_fluff=True,
            min_content_quality=0.3
        )

        # Verify result structure
        assert isinstance(result, TagAnalysisResult)
        assert isinstance(result.topic_groups, list)
        assert isinstance(result.actionable_insights, list)
        assert isinstance(result.theoretical_insights, list)
        assert isinstance(result.tag_hierarchy, dict)
        assert isinstance(result.content_statistics, dict)
        assert isinstance(result.quality_metrics, dict)

        # Verify content statistics
        stats = result.content_statistics
        assert 'total_files' in stats
        assert 'total_words' in stats
        assert 'unique_tags' in stats
        assert 'average_quality_score' in stats

    def test_tag_pattern_matching(self, tag_analysis_engine, mock_query_engine):
        """Test different tag pattern matching scenarios."""
        # Test wildcard patterns
        patterns = ['ai/*', 'development/tools']

        # Mock query execution
        mock_result = Mock(spec=QueryResult)
        mock_result.rows = []
        mock_query_engine.execute_query.return_value = mock_result

        # Should not raise error with empty results
        result = tag_analysis_engine.comprehensive_tag_analysis(
            tag_patterns=patterns,
            grouping_strategy='semantic'
        )

        assert isinstance(result, TagAnalysisResult)
        assert len(result.topic_groups) == 0

    def test_grouping_strategies(self, tag_analysis_engine, mock_query_engine, sample_content_data):
        """Test different content grouping strategies."""
        # Mock the query engine
        mock_result = Mock(spec=QueryResult)
        mock_result.rows = [
            {
                'id': item['id'],
                'path': item['path'],
                'word_count': item['word_count'],
                'heading_count': item['heading_count'],
                'created_date': item['created_date'],
                'modified_date': item['modified_date'],
                'content': item['content'],
                'headings': item['headings'],
                'all_tags': ','.join(item['tags']),
                'title': item['title'],
                'description': item['description'],
                'category': item['category']
            }
            for item in sample_content_data
        ]
        mock_query_engine.execute_query.return_value = mock_result

        # Test semantic grouping
        result_semantic = tag_analysis_engine.comprehensive_tag_analysis(
            tag_patterns=['ai'],
            grouping_strategy='semantic'
        )

        # Test hierarchical grouping
        result_hierarchy = tag_analysis_engine.comprehensive_tag_analysis(
            tag_patterns=['ai'],
            grouping_strategy='tag-hierarchy'
        )

        # Test temporal grouping
        result_temporal = tag_analysis_engine.comprehensive_tag_analysis(
            tag_patterns=['ai'],
            grouping_strategy='temporal'
        )

        # All should return valid results
        assert isinstance(result_semantic, TagAnalysisResult)
        assert isinstance(result_hierarchy, TagAnalysisResult)
        assert isinstance(result_temporal, TagAnalysisResult)


class TestTagAnalysisMCPIntegration:
    """Test MCP server integration for tag analysis."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP server for testing."""
        from mdquery.mcp import MDQueryMCPServer

        with patch('mdquery.mcp.DatabaseManager'), \
             patch('mdquery.mcp.QueryEngine'), \
             patch('mdquery.mcp.Indexer'), \
             patch('mdquery.mcp.CacheManager'):

            server = MDQueryMCPServer()
            server.db_manager = Mock()
            server.query_engine = Mock()
            server.indexer = Mock()
            server.cache_manager = Mock()
            server._initialization_successful = True

            return server

    @pytest.mark.asyncio
    async def test_comprehensive_tag_analysis_mcp_tool(self, mock_mcp_server):
        """Test the MCP tool for comprehensive tag analysis."""
        # Mock the tag analysis engine
        mock_analysis_result = TagAnalysisResult(
            topic_groups=[
                TopicGroup(
                    name="AI Development",
                    documents=[{
                        'id': 1,
                        'path': '/test.md',
                        'title': 'Test',
                        'word_count': 100,
                        'tags': ['ai', 'development'],
                        'quality_score': 0.8
                    }],
                    key_themes=['ai', 'development'],
                    related_groups=[],
                    tag_patterns=['ai', 'development'],
                    content_quality_score=0.8
                )
            ],
            actionable_insights=[
                ActionableInsight(
                    title="Test Insight",
                    description="Test actionable insight",
                    implementation_difficulty="medium",
                    expected_impact="high",
                    category="tools",
                    source_files=['/test.md'],
                    confidence_score=0.9
                )
            ],
            theoretical_insights=[
                TheoreticalInsight(
                    title="Test Theory",
                    description="Test theoretical insight",
                    related_concepts=['ai', 'theory'],
                    research_directions=['explore further'],
                    source_files=['/test.md'],
                    confidence_score=0.8
                )
            ],
            tag_hierarchy={'ai': ['ai/agents']},
            content_statistics={'total_files': 1},
            quality_metrics={'content_coverage': 1.0}
        )

        # Mock the TagAnalysisEngine
        with patch('mdquery.mcp.TagAnalysisEngine') as mock_tag_engine_class:
            mock_tag_engine = Mock()
            mock_tag_engine.comprehensive_tag_analysis.return_value = mock_analysis_result
            mock_tag_engine_class.return_value = mock_tag_engine

            # Find the comprehensive_tag_analysis tool
            tools = mock_mcp_server.server._tools
            tag_analysis_tool = None

            for tool_name, tool_func in tools.items():
                if 'comprehensive_tag_analysis' in tool_name:
                    tag_analysis_tool = tool_func
                    break

            assert tag_analysis_tool is not None, "comprehensive_tag_analysis tool not found"

            # Test the tool
            result_json = await tag_analysis_tool(
                tag_patterns="ai,development",
                grouping_strategy="semantic",
                include_actionable=True,
                include_theoretical=True,
                remove_fluff=True,
                min_content_quality=0.3
            )

            # Parse and verify result
            result = json.loads(result_json)

            assert 'topic_groups' in result
            assert 'actionable_insights' in result
            assert 'theoretical_insights' in result
            assert 'tag_hierarchy' in result
            assert 'content_statistics' in result
            assert 'quality_metrics' in result

            # Verify topic groups structure
            assert len(result['topic_groups']) == 1
            group = result['topic_groups'][0]
            assert group['name'] == "AI Development"
            assert group['document_count'] == 1
            assert len(group['documents']) == 1

            # Verify insights structure
            assert len(result['actionable_insights']) == 1
            actionable = result['actionable_insights'][0]
            assert actionable['title'] == "Test Insight"
            assert actionable['implementation_difficulty'] == "medium"
            assert actionable['expected_impact'] == "high"

            assert len(result['theoretical_insights']) == 1
            theoretical = result['theoretical_insights'][0]
            assert theoretical['title'] == "Test Theory"
            assert isinstance(theoretical['related_concepts'], list)

    @pytest.mark.asyncio
    async def test_tag_analysis_error_handling(self, mock_mcp_server):
        """Test error handling in the MCP tag analysis tool."""
        # Mock TagAnalysisEngine to raise an exception
        with patch('mdquery.mcp.TagAnalysisEngine') as mock_tag_engine_class:
            mock_tag_engine = Mock()
            mock_tag_engine.comprehensive_tag_analysis.side_effect = Exception("Test error")
            mock_tag_engine_class.return_value = mock_tag_engine

            # Find the tool
            tools = mock_mcp_server.server._tools
            tag_analysis_tool = None

            for tool_name, tool_func in tools.items():
                if 'comprehensive_tag_analysis' in tool_name:
                    tag_analysis_tool = tool_func
                    break

            # Test error handling
            with pytest.raises(Exception) as exc_info:
                await tag_analysis_tool(
                    tag_patterns="ai",
                    grouping_strategy="semantic"
                )

            assert "Comprehensive tag analysis failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_tag_patterns_error(self, mock_mcp_server):
        """Test error handling for empty tag patterns."""
        # Find the tool
        tools = mock_mcp_server.server._tools
        tag_analysis_tool = None

        for tool_name, tool_func in tools.items():
            if 'comprehensive_tag_analysis' in tool_name:
                tag_analysis_tool = tool_func
                break

        # Test with empty tag patterns
        with pytest.raises(Exception) as exc_info:
            await tag_analysis_tool(
                tag_patterns="",
                grouping_strategy="semantic"
            )

        assert "At least one tag pattern must be provided" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])