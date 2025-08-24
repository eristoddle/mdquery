"""
Simple integration test for query guidance system.

Tests that the query guidance system integrates properly with the MCP server
by testing the core functionality without complex MCP protocol details.
"""

import pytest
import json
from pathlib import Path

from mdquery.query_guidance import QueryGuidanceEngine
from mdquery.mcp import MDQueryMCPServer
from mdquery.config import SimplifiedConfig


class TestQueryGuidanceSimpleIntegration:
    """Test query guidance system integration."""

    def test_query_guidance_engine_initialization(self):
        """Test that the query guidance engine initializes correctly."""
        engine = QueryGuidanceEngine()

        # Verify all components are initialized
        assert len(engine.templates) > 0
        assert len(engine.optimizations) > 0
        assert len(engine.common_patterns) > 0
        assert 'tables' in engine.syntax_reference

        # Verify we have templates for all required categories
        categories = set(template.category for template in engine.templates)
        expected_categories = {'tag-analysis', 'workflow', 'content', 'research', 'performance'}
        assert expected_categories.issubset(categories)

        # Verify we have templates for all complexity levels
        complexities = set(template.complexity for template in engine.templates)
        expected_complexities = {'basic', 'intermediate', 'advanced'}
        assert expected_complexities.issubset(complexities)

    def test_mcp_server_query_guidance_integration(self, tmp_path):
        """Test that MCP server can initialize query guidance engine."""
        # Create test notes directory
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create simplified config
        config = SimplifiedConfig(
            notes_dir=str(notes_dir),
            auto_index=False  # Skip indexing for this test
        )

        # Create MCP server
        server = MDQueryMCPServer(config=config)

        # Verify query guidance engine can be initialized
        assert server.query_guidance_engine is None

        # Initialize it
        server.query_guidance_engine = QueryGuidanceEngine()

        # Verify it works
        assert server.query_guidance_engine is not None
        assert len(server.query_guidance_engine.templates) > 0

    def test_tag_analysis_guidance_workflow(self):
        """Test the complete workflow for tag analysis guidance."""
        engine = QueryGuidanceEngine()

        # Get guidance for tag analysis
        guidance = engine.get_query_guidance(
            analysis_type="tag-analysis",
            content_description="AI development notes with hierarchical tags"
        )

        # Verify we get relevant templates
        assert len(guidance.suggested_queries) > 0

        # Should include basic and hierarchical tag templates
        template_names = [t.name for t in guidance.suggested_queries]
        basic_tag_template = any("Basic Tag" in name for name in template_names)
        hierarchical_template = any("Hierarchical" in name for name in template_names)

        assert basic_tag_template or hierarchical_template  # At least one should be present

        # Verify optimization tips are relevant
        assert len(guidance.optimization_tips) > 0
        tag_related_tips = any("tag" in tip.lower() for tip in guidance.optimization_tips)
        assert tag_related_tips

        # Verify examples are provided
        assert len(guidance.examples) > 0

        # Verify syntax reference is complete
        assert 'tables' in guidance.syntax_reference
        assert 'tags' in guidance.syntax_reference['tables']

    def test_workflow_analysis_guidance_workflow(self):
        """Test the complete workflow for workflow analysis guidance."""
        engine = QueryGuidanceEngine()

        # Get guidance for workflow analysis
        guidance = engine.get_query_guidance(
            analysis_type="workflow",
            content_description="Development process improvement analysis"
        )

        # Verify we get relevant templates
        assert len(guidance.suggested_queries) > 0

        # Should include workflow-related templates
        workflow_templates = [t for t in guidance.suggested_queries if 'workflow' in t.category.lower()]
        assert len(workflow_templates) > 0

        # Verify workflow-specific tips
        workflow_tips = [tip for tip in guidance.optimization_tips if 'workflow' in tip.lower()]
        assert len(workflow_tips) > 0

    def test_query_optimization_workflow(self):
        """Test the complete workflow for query optimization."""
        engine = QueryGuidanceEngine()

        # Test with a query that needs optimization
        bad_query = "SELECT * FROM files WHERE content LIKE '%python%'"
        suggestions = engine.get_optimization_suggestions(bad_query)

        # Should get FTS suggestion
        assert len(suggestions) > 0
        fts_suggestion = next((s for s in suggestions if 'fts' in s.suggestion.lower()), None)
        assert fts_suggestion is not None
        assert fts_suggestion.performance_impact == 'high'

        # Test with a good query
        good_query = """SELECT f.filename, COUNT(t.tag) as tag_count
                       FROM files f
                       JOIN tags t ON f.id = t.file_id
                       WHERE t.tag IN ('ai', 'llm')
                       GROUP BY f.id
                       ORDER BY tag_count DESC
                       LIMIT 20"""

        suggestions = engine.get_optimization_suggestions(good_query)
        # Should have few or no suggestions for a well-optimized query
        assert len(suggestions) <= 2

    def test_template_filtering_workflow(self):
        """Test the complete workflow for template filtering."""
        engine = QueryGuidanceEngine()

        # Test category filtering
        tag_templates = engine.get_query_templates(category="tag-analysis")
        assert len(tag_templates) > 0
        assert all(t.category == "tag-analysis" for t in tag_templates)

        workflow_templates = engine.get_query_templates(category="workflow")
        assert len(workflow_templates) > 0
        assert all(t.category == "workflow" for t in workflow_templates)

        # Test complexity filtering
        basic_templates = engine.get_query_templates(complexity="basic")
        assert len(basic_templates) > 0
        assert all(t.complexity == "basic" for t in basic_templates)

        advanced_templates = engine.get_query_templates(complexity="advanced")
        assert len(advanced_templates) > 0
        assert all(t.complexity == "advanced" for t in advanced_templates)

        # Test combined filtering
        basic_tag_templates = engine.get_query_templates(
            category="tag-analysis",
            complexity="basic"
        )
        assert len(basic_tag_templates) > 0
        assert all(t.category == "tag-analysis" and t.complexity == "basic"
                  for t in basic_tag_templates)

    def test_json_serialization_workflow(self):
        """Test that all components can be serialized to JSON."""
        engine = QueryGuidanceEngine()

        # Test engine serialization
        engine_dict = engine.to_dict()
        json_str = json.dumps(engine_dict, default=str)
        assert len(json_str) > 0

        # Test guidance serialization
        guidance = engine.get_query_guidance("tag-analysis")

        # Manually create a serializable version (like the MCP tools do)
        result_data = {
            'analysis_type': "tag-analysis",
            'suggested_queries': [],
            'optimization_tips': guidance.optimization_tips,
            'common_patterns': guidance.common_patterns,
            'syntax_reference': guidance.syntax_reference,
            'examples': guidance.examples
        }

        # Convert suggested queries
        for template in guidance.suggested_queries:
            template_data = {
                'name': template.name,
                'description': template.description,
                'category': template.category,
                'sql_template': template.sql_template,
                'parameters': [
                    {
                        'name': param.name,
                        'type': param.type,
                        'description': param.description,
                        'default': param.default,
                        'required': param.required,
                        'examples': param.examples
                    }
                    for param in template.parameters
                ],
                'example_usage': template.example_usage,
                'complexity': template.complexity,
                'performance_notes': template.performance_notes
            }
            result_data['suggested_queries'].append(template_data)

        # Should be JSON serializable
        json_str = json.dumps(result_data, default=str)
        assert len(json_str) > 0

        # Should be parseable
        parsed_data = json.loads(json_str)
        assert parsed_data['analysis_type'] == "tag-analysis"
        assert len(parsed_data['suggested_queries']) > 0

    def test_requirements_coverage(self):
        """Test that all requirements 5.1-5.5 are covered."""
        engine = QueryGuidanceEngine()

        # Requirement 5.1: Query syntax documentation
        syntax_ref = engine.syntax_reference
        assert 'tables' in syntax_ref
        assert 'operators' in syntax_ref
        assert 'functions' in syntax_ref
        assert 'fts_syntax' in syntax_ref

        # Requirement 5.2: Common patterns for tag-based analysis
        guidance = engine.get_query_guidance("tag-analysis")
        tag_patterns = [p for p in guidance.common_patterns if 'tag' in p.lower()]
        assert len(tag_patterns) > 0

        # Requirement 5.3: Templates for multi-dimensional analysis
        advanced_templates = engine.get_query_templates(complexity="advanced")
        multi_dimensional = [t for t in advanced_templates if 'WITH' in t.sql_template]  # CTEs indicate complexity
        assert len(multi_dimensional) > 0

        # Requirement 5.4: Optimal query approaches for specific analysis types
        workflow_guidance = engine.get_query_guidance("workflow")
        assert len(workflow_guidance.suggested_queries) > 0
        assert len(workflow_guidance.optimization_tips) > 0

        # Requirement 5.5: Query optimization suggestions
        bad_query = "SELECT * FROM files WHERE content LIKE '%test%'"
        suggestions = engine.get_optimization_suggestions(bad_query)
        assert len(suggestions) > 0
        performance_suggestions = [s for s in suggestions if s.performance_impact in ['medium', 'high']]
        assert len(performance_suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__])