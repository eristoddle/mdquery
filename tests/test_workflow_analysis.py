"""
Tests for workflow analysis engine.

This module tests the WorkflowAnalyzer class and its integration with the MCP server.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from mdquery.workflow_analysis import WorkflowAnalyzer, ImprovementOpportunity, WorkflowPattern
from mdquery.query import QueryEngine
from mdquery.database import DatabaseManager
from mdquery.models import QueryResult


class TestWorkflowAnalyzer:
    """Test cases for WorkflowAnalyzer class."""

    @pytest.fixture
    def mock_query_engine(self):
        """Create a mock query engine for testing."""
        mock_engine = Mock(spec=QueryEngine)

        # Mock query result for development content
        mock_result = QueryResult(
            rows=[
                {
                    'id': 1,
                    'path': '/test/mcp-development.md',
                    'word_count': 500,
                    'heading_count': 3,
                    'created_date': '2024-01-01',
                    'modified_date': '2024-01-15',
                    'content': 'This document discusses MCP server development and automation opportunities. We need to automate the deployment process and improve testing workflows.',
                    'headings': 'MCP Development\nAutomation\nTesting',
                    'all_tags': 'mcp,development,automation,testing',
                    'title': 'MCP Development Guide',
                    'description': 'Guide for MCP development',
                    'category': 'development'
                },
                {
                    'id': 2,
                    'path': '/test/ai-agents.md',
                    'word_count': 300,
                    'heading_count': 2,
                    'created_date': '2024-01-02',
                    'modified_date': '2024-01-16',
                    'content': 'AI agents require careful design and implementation. Manual processes are time consuming and error prone.',
                    'headings': 'AI Agents\nImplementation',
                    'all_tags': 'ai,agents,implementation',
                    'title': 'AI Agent Implementation',
                    'description': 'AI agent implementation notes',
                    'category': 'ai'
                }
            ],
            columns=['id', 'path', 'word_count', 'heading_count', 'created_date', 'modified_date', 'content', 'headings', 'all_tags', 'title', 'description', 'category'],
            row_count=2,
            execution_time_ms=10.0,
            query="SELECT * FROM test"
        )

        mock_engine.execute_query.return_value = mock_result
        return mock_engine

    @pytest.fixture
    def workflow_analyzer(self, mock_query_engine):
        """Create a WorkflowAnalyzer instance for testing."""
        return WorkflowAnalyzer(mock_query_engine)

    def test_workflow_analyzer_initialization(self, workflow_analyzer):
        """Test that WorkflowAnalyzer initializes correctly."""
        assert workflow_analyzer.query_engine is not None
        assert workflow_analyzer.tag_analyzer is not None
        assert 'mcp' in workflow_analyzer.development_keywords
        assert 'process_gaps' in workflow_analyzer.improvement_patterns

    def test_build_development_tag_patterns(self, workflow_analyzer):
        """Test building development-focused tag patterns."""
        # Test with specific focus areas
        patterns = workflow_analyzer._build_development_tag_patterns(['mcp', 'agents'])
        assert 'mcp' in patterns
        assert 'mcp/*' in patterns
        assert 'agents' in patterns

        # Test with default patterns
        default_patterns = workflow_analyzer._build_development_tag_patterns(None)
        assert 'ai/*' in default_patterns
        assert 'mcp/*' in default_patterns
        assert 'automation/*' in default_patterns

    def test_classify_pattern_type(self, workflow_analyzer):
        """Test pattern type classification."""
        positive_content = "This automation is working well and improved our efficiency"
        negative_content = "This manual process is slow and error prone"
        neutral_content = "This is a standard development approach"

        assert workflow_analyzer._classify_pattern_type(positive_content, []) == "positive"
        assert workflow_analyzer._classify_pattern_type(negative_content, []) == "negative"
        assert workflow_analyzer._classify_pattern_type(neutral_content, []) == "neutral"

    def test_estimate_opportunity_difficulty(self, workflow_analyzer):
        """Test difficulty estimation for improvement opportunities."""
        simple_content = "This is a simple automation task"
        complex_content = "This requires complex enterprise architecture integration"

        # Test process gaps (base: medium)
        assert workflow_analyzer._estimate_opportunity_difficulty('process_gaps', simple_content) == 'medium'
        assert workflow_analyzer._estimate_opportunity_difficulty('process_gaps', complex_content) == 'high'

        # Test tool opportunities (base: low)
        assert workflow_analyzer._estimate_opportunity_difficulty('tool_opportunities', simple_content) == 'low'
        assert workflow_analyzer._estimate_opportunity_difficulty('tool_opportunities', complex_content) == 'medium'

    def test_estimate_opportunity_impact(self, workflow_analyzer):
        """Test impact estimation for improvement opportunities."""
        # Test with different file counts and categories
        assert workflow_analyzer._estimate_opportunity_impact('process_gaps', 15) == 'high'  # High base + many files
        assert workflow_analyzer._estimate_opportunity_impact('process_gaps', 2) == 'medium'  # High base + few files
        assert workflow_analyzer._estimate_opportunity_impact('tool_opportunities', 10) == 'high'  # Medium base + many files -> high

    def test_calculate_priority_score(self, workflow_analyzer):
        """Test priority score calculation."""
        # High impact, low difficulty should have high priority
        high_priority = workflow_analyzer._calculate_priority_score('low', 'high', 5)
        assert high_priority > 0.7

        # Low impact, high difficulty should have low priority
        low_priority = workflow_analyzer._calculate_priority_score('high', 'low', 2)
        assert low_priority < 0.5

        # Medium values should be in between
        medium_priority = workflow_analyzer._calculate_priority_score('medium', 'medium', 3)
        assert 0.4 < medium_priority < 0.8

    def test_generate_suggested_actions(self, workflow_analyzer):
        """Test generation of suggested actions."""
        process_actions = workflow_analyzer._generate_suggested_actions('process_gaps', [])
        assert len(process_actions) > 0
        assert any('process' in action.lower() for action in process_actions)

        tool_actions = workflow_analyzer._generate_suggested_actions('tool_opportunities', [])
        assert len(tool_actions) > 0
        assert any('tool' in action.lower() or 'automat' in action.lower() for action in tool_actions)

    @patch('mdquery.workflow_analysis.TagAnalysisEngine')
    def test_analyze_development_workflow(self, mock_tag_engine_class, workflow_analyzer):
        """Test the main workflow analysis method."""
        # Mock the tag analysis engine
        mock_tag_engine = Mock()
        mock_tag_engine_class.return_value = mock_tag_engine

        # Mock tag analysis result
        from mdquery.tag_analysis import TagAnalysisResult, TopicGroup
        mock_topic_group = TopicGroup(
            name="MCP Development",
            documents=[
                {
                    'id': 1,
                    'path': '/test/mcp.md',
                    'content': 'MCP development requires automation and better tools',
                    'tags': ['mcp', 'development'],
                    'quality_score': 0.8
                }
            ],
            key_themes=['mcp', 'development'],
            related_groups=[],
            tag_patterns=['mcp', 'development'],
            content_quality_score=0.8
        )

        mock_analysis = TagAnalysisResult(
            topic_groups=[mock_topic_group],
            actionable_insights=[],
            theoretical_insights=[],
            tag_hierarchy={'mcp': ['mcp/server', 'mcp/tools']},
            content_statistics={'total_files': 1},
            quality_metrics={'content_coverage': 1.0}
        )

        mock_tag_engine.comprehensive_tag_analysis.return_value = mock_analysis

        # Run analysis
        result = workflow_analyzer.analyze_development_workflow(
            focus_areas=['mcp', 'automation'],
            improvement_categories=['process', 'tools']
        )

        # Verify results
        assert result is not None
        assert len(result.topic_groups) > 0
        assert result.development_metrics is not None
        assert result.recommendations is not None
        assert 'immediate_actions' in result.recommendations

    def test_calculate_workflow_maturity(self, workflow_analyzer):
        """Test workflow maturity calculation."""
        from mdquery.tag_analysis import TagAnalysisResult, ActionableInsight

        # Create mock insights with different categories
        insights = [
            ActionableInsight(
                title="Test",
                description="Test",
                implementation_difficulty="low",
                expected_impact="high",
                category="automation",
                source_files=[],
                confidence_score=0.8
            ),
            ActionableInsight(
                title="Test2",
                description="Test2",
                implementation_difficulty="medium",
                expected_impact="medium",
                category="process",
                source_files=[],
                confidence_score=0.7
            )
        ]

        mock_analysis = TagAnalysisResult(
            topic_groups=[],
            actionable_insights=insights,
            theoretical_insights=[],
            tag_hierarchy={},
            content_statistics={},
            quality_metrics={}
        )

        maturity_score = workflow_analyzer._calculate_workflow_maturity(mock_analysis)
        assert 0.0 <= maturity_score <= 1.0

    def test_improvement_opportunity_creation(self, workflow_analyzer):
        """Test creation of improvement opportunities."""
        from mdquery.tag_analysis import TopicGroup

        mock_group = TopicGroup(
            name="Test Group",
            documents=[],
            key_themes=[],
            related_groups=[],
            tag_patterns=[],
            content_quality_score=0.5
        )

        opportunity = workflow_analyzer._create_improvement_opportunity(
            'process_gaps',
            ['manual process', 'time consuming'],
            mock_group,
            ['/test/file.md'],
            'manual process that is time consuming'
        )

        assert isinstance(opportunity, ImprovementOpportunity)
        assert opportunity.category == 'process'
        assert opportunity.implementation_difficulty in ['low', 'medium', 'high']
        assert opportunity.expected_impact in ['low', 'medium', 'high']
        assert 0.0 <= opportunity.priority_score <= 1.0
        assert len(opportunity.suggested_actions) > 0


class TestWorkflowAnalysisIntegration:
    """Integration tests for workflow analysis with MCP server."""

    def test_workflow_analysis_data_structures(self):
        """Test that workflow analysis data structures are properly defined."""
        from mdquery.workflow_analysis import ImprovementOpportunity, WorkflowPattern, WorkflowAnalysisResult

        # Test ImprovementOpportunity
        opportunity = ImprovementOpportunity(
            title="Test Opportunity",
            description="Test description",
            category="process",
            implementation_difficulty="medium",
            expected_impact="high",
            priority_score=0.8,
            source_files=["/test/file.md"],
            related_patterns=["manual process"],
            suggested_actions=["Automate the process"]
        )

        assert opportunity.title == "Test Opportunity"
        assert opportunity.priority_score == 0.8

        # Test WorkflowPattern
        pattern = WorkflowPattern(
            pattern_name="Test Pattern",
            description="Test pattern description",
            frequency=5,
            files_involved=["/test/file.md"],
            tags_involved=["test"],
            pattern_type="positive",
            confidence_score=0.9
        )

        assert pattern.pattern_name == "Test Pattern"
        assert pattern.confidence_score == 0.9

        # Test WorkflowAnalysisResult
        result = WorkflowAnalysisResult(
            topic_groups=[],
            actionable_insights=[],
            theoretical_insights=[],
            improvement_opportunities=[opportunity],
            workflow_patterns=[pattern],
            development_metrics={},
            recommendations={}
        )

        assert len(result.improvement_opportunities) == 1
        assert len(result.workflow_patterns) == 1

    def test_development_keywords_coverage(self):
        """Test that development keywords cover expected areas."""
        from mdquery.workflow_analysis import WorkflowAnalyzer
        from mdquery.query import QueryEngine

        # Create analyzer with mock query engine
        mock_engine = Mock(spec=QueryEngine)
        analyzer = WorkflowAnalyzer(mock_engine)

        # Check that key development areas are covered
        expected_areas = ['mcp', 'agents', 'automation', 'coding', 'testing']
        for area in expected_areas:
            assert area in analyzer.development_keywords
            assert len(analyzer.development_keywords[area]) > 0

    def test_improvement_patterns_coverage(self):
        """Test that improvement patterns cover expected categories."""
        from mdquery.workflow_analysis import WorkflowAnalyzer
        from mdquery.query import QueryEngine

        # Create analyzer with mock query engine
        mock_engine = Mock(spec=QueryEngine)
        analyzer = WorkflowAnalyzer(mock_engine)

        # Check that key improvement categories are covered
        expected_categories = ['process_gaps', 'tool_opportunities', 'quality_issues', 'knowledge_gaps']
        for category in expected_categories:
            assert category in analyzer.improvement_patterns
            assert len(analyzer.improvement_patterns[category]) > 0


if __name__ == "__main__":
    pytest.main([__file__])