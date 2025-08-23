"""
Simple tests for comprehensive tag analysis functionality.

This module tests the core TagAnalysisEngine functionality without complex MCP integration.
"""

import pytest
from unittest.mock import Mock

from mdquery.tag_analysis import TagAnalysisEngine, TagAnalysisResult, TopicGroup, ActionableInsight, TheoreticalInsight
from mdquery.query import QueryEngine
from mdquery.models import QueryResult


class TestTagAnalysisEngineCore:
    """Test core TagAnalysisEngine functionality."""

    @pytest.fixture
    def mock_query_engine(self):
        """Create a mock query engine for testing."""
        mock_engine = Mock(spec=QueryEngine)
        return mock_engine

    @pytest.fixture
    def tag_analysis_engine(self, mock_query_engine):
        """Create TagAnalysisEngine instance for testing."""
        return TagAnalysisEngine(mock_query_engine)

    def test_engine_initialization(self, mock_query_engine):
        """Test TagAnalysisEngine initialization."""
        engine = TagAnalysisEngine(mock_query_engine)
        assert engine.query_engine == mock_query_engine
        assert len(engine.actionable_keywords) > 0
        assert len(engine.theoretical_keywords) > 0
        assert len(engine.fluff_indicators) > 0

    def test_content_quality_calculation(self, tag_analysis_engine):
        """Test content quality score calculation."""
        # High quality content
        high_quality_item = {
            'content': 'This is a comprehensive guide on implementing AI agents using modern frameworks. The process involves setting up the development environment, configuring the agent architecture, and testing the implementation.',
            'title': 'AI Agent Development Guide',
            'tags': ['ai', 'agents', 'development', 'implementation'],
            'word_count': 500,
            'heading_count': 3
        }

        score = tag_analysis_engine._calculate_content_quality_score(high_quality_item)
        assert score > 0.5, f"Expected high quality score, got {score}"

        # Low quality content
        low_quality_item = {
            'content': 'quick note reminder',
            'title': 'Quick Note',
            'tags': ['reminder', 'todo'],
            'word_count': 20,
            'heading_count': 0
        }

        score = tag_analysis_engine._calculate_content_quality_score(low_quality_item)
        assert score < 0.7, f"Expected lower quality score, got {score}"

    def test_tag_hierarchy_building(self, tag_analysis_engine):
        """Test hierarchical tag structure building."""
        content_list = [
            {'tags': ['ai/agents', 'ai/llm', 'development/tools']},
            {'tags': ['ai/research', 'theory', 'ai/applications']}
        ]

        hierarchy = tag_analysis_engine._build_tag_hierarchy(content_list)

        # Check hierarchical relationships
        assert 'ai' in hierarchy
        assert 'ai/agents' in hierarchy['ai']
        assert 'ai/llm' in hierarchy['ai']
        assert 'development' in hierarchy

    def test_insight_category_determination(self, tag_analysis_engine):
        """Test actionable insight category determination."""
        # Process category
        process_content = "workflow methodology approach procedure"
        category = tag_analysis_engine._determine_insight_category(process_content, "", [])
        assert category == 'process'

        # Tools category
        tools_content = "software framework library tool application"
        category = tag_analysis_engine._determine_insight_category(tools_content, "", [])
        assert category == 'tools'

        # Automation category
        automation_content = "automation script automated ci/cd pipeline"
        category = tag_analysis_engine._determine_insight_category(automation_content, "", [])
        assert category == 'automation'

    def test_implementation_difficulty_estimation(self, tag_analysis_engine):
        """Test implementation difficulty estimation."""
        # Easy implementation
        easy_content = "simple easy quick basic straightforward"
        difficulty = tag_analysis_engine._estimate_implementation_difficulty(easy_content, [])
        assert difficulty == 'low'

        # Hard implementation
        hard_content = "complex advanced difficult challenging enterprise scale"
        difficulty = tag_analysis_engine._estimate_implementation_difficulty(hard_content, [])
        assert difficulty == 'high'

        # Medium implementation (default)
        medium_content = "standard implementation requires some work"
        difficulty = tag_analysis_engine._estimate_implementation_difficulty(medium_content, [])
        assert difficulty == 'medium'

    def test_impact_estimation(self, tag_analysis_engine):
        """Test expected impact estimation."""
        # High impact
        high_impact_content = "productivity efficiency performance scalability security"
        impact = tag_analysis_engine._estimate_impact(high_impact_content, ['performance'])
        assert impact == 'high'

        # Low impact
        low_impact_content = "minor change small update"
        impact = tag_analysis_engine._estimate_impact(low_impact_content, [])
        assert impact == 'low'

    def test_content_statistics_calculation(self, tag_analysis_engine):
        """Test content statistics calculation."""
        content_list = [
            {
                'word_count': 500,
                'heading_count': 3,
                'tags': ['ai', 'development'],
                'quality_score': 0.8
            },
            {
                'word_count': 300,
                'heading_count': 2,
                'tags': ['ai', 'research'],
                'quality_score': 0.7
            }
        ]

        stats = tag_analysis_engine._calculate_content_statistics(content_list)

        assert stats['total_files'] == 2
        assert stats['total_words'] == 800
        assert stats['average_words_per_file'] == 400
        assert stats['unique_tags'] == 3  # ai, development, research
        assert stats['average_quality_score'] == 0.75

    def test_quality_metrics_calculation(self, tag_analysis_engine):
        """Test quality metrics calculation."""
        content_list = [
            {'id': 1, 'tags': ['ai/agents', 'development']},
            {'id': 2, 'tags': ['ai/research', 'theory']}
        ]

        topic_groups = [
            TopicGroup(
                name="AI Development",
                documents=[{'id': 1}],
                key_themes=['ai'],
                related_groups=[],
                tag_patterns=['ai'],
                content_quality_score=0.8
            )
        ]

        metrics = tag_analysis_engine._calculate_quality_metrics(content_list, topic_groups)

        assert 'content_coverage' in metrics
        assert 'average_group_quality' in metrics
        assert 'hierarchy_utilization' in metrics
        assert 'analysis_completeness' in metrics

        # Coverage should be 0.5 (1 out of 2 files grouped)
        assert metrics['content_coverage'] == 0.5
        assert metrics['average_group_quality'] == 0.8

    def test_mcp_integration_import(self):
        """Test that TagAnalysisEngine can be imported in MCP context."""
        # Test that the import works
        from mdquery.tag_analysis import TagAnalysisEngine
        from mdquery.mcp import TagAnalysisEngine as MCPTagAnalysisEngine

        # Verify they are the same class
        assert TagAnalysisEngine == MCPTagAnalysisEngine


if __name__ == "__main__":
    pytest.main([__file__])