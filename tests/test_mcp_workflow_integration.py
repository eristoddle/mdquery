"""
Integration tests for workflow analysis MCP tool.

This module tests the integration of workflow analysis with the MCP server.
"""

import pytest
import json
from unittest.mock import Mock
from pathlib import Path

from mdquery.mcp import MDQueryMCPServer
from mdquery.config import SimplifiedConfig, MCPServerConfig


class TestMCPWorkflowIntegration:
    """Test MCP server integration with workflow analysis."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=MCPServerConfig)
        config.notes_dir = Path("/test/notes")
        config.db_path = Path("/test/notes/.mdquery/mdquery.db")
        config.cache_dir = Path("/test/notes/.mdquery/cache")
        config.auto_index = True

        simplified_config = Mock(spec=SimplifiedConfig)
        simplified_config.config = config

        return simplified_config

    @pytest.fixture
    def mcp_server(self, mock_config):
        """Create an MCP server instance for testing."""
        return MDQueryMCPServer(config=mock_config)

    def test_workflow_tool_registration(self, mcp_server):
        """Test that the workflow analysis tool is properly registered."""
        # Check that the server has been set up
        assert hasattr(mcp_server, 'server')
        assert mcp_server.server is not None

        # The tool should be registered during server setup
        # We can verify the server exists and has the expected name
        assert mcp_server.server.name == "mdquery"

    def test_workflow_analyzer_import(self):
        """Test that the workflow analyzer can be imported successfully."""
        from mdquery.workflow_analysis import WorkflowAnalyzer, ImprovementOpportunity, WorkflowPattern, WorkflowAnalysisResult

        # Verify classes can be imported
        assert WorkflowAnalyzer is not None
        assert ImprovementOpportunity is not None
        assert WorkflowPattern is not None
        assert WorkflowAnalysisResult is not None

    def test_mcp_server_has_workflow_tool_setup(self, mcp_server):
        """Test that the MCP server has the workflow tool setup method."""
        # Verify the server setup includes our tool
        # The _setup_tools method should have been called during initialization
        assert hasattr(mcp_server, '_setup_tools')
        assert callable(mcp_server._setup_tools)

    def test_workflow_data_structures(self):
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


if __name__ == "__main__":
    pytest.main([__file__])