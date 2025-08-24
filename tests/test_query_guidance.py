"""
Tests for query guidance system.

Tests the query guidance engine, templates, optimization suggestions,
and MCP tool integration for requirements 5.1-5.5.
"""

import pytest
import json
from pathlib import Path

from mdquery.query_guidance import (
    QueryGuidanceEngine, QueryTemplate, QueryParameter,
    QueryOptimization, QueryGuidance
)


class TestQueryGuidanceEngine:
    """Test the QueryGuidanceEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QueryGuidanceEngine()

    def test_initialization(self):
        """Test that the engine initializes with templates and references."""
        assert len(self.engine.templates) > 0
        assert len(self.engine.optimizations) > 0
        assert 'tables' in self.engine.syntax_reference
        assert len(self.engine.common_patterns) > 0

    def test_get_query_guidance_tag_analysis(self):
        """Test getting guidance for tag analysis."""
        guidance = self.engine.get_query_guidance(
            analysis_type="tag-analysis",
            content_description="AI development notes"
        )

        assert isinstance(guidance, QueryGuidance)
        assert len(guidance.suggested_queries) > 0
        assert len(guidance.optimization_tips) > 0
        assert len(guidance.common_patterns) > 0
        assert 'tables' in guidance.syntax_reference
        assert len(guidance.examples) > 0

        # Check that tag-related templates are included
        tag_templates = [t for t in guidance.suggested_queries if 'tag' in t.name.lower()]
        assert len(tag_templates) > 0

    def test_get_query_guidance_workflow_analysis(self):
        """Test getting guidance for workflow analysis."""
        guidance = self.engine.get_query_guidance(
            analysis_type="workflow",
            content_description="Development process analysis"
        )

        assert isinstance(guidance, QueryGuidance)
        assert len(guidance.suggested_queries) > 0

        # Check that workflow-related templates are included
        workflow_templates = [t for t in guidance.suggested_queries if 'workflow' in t.category.lower()]
        assert len(workflow_templates) > 0

    def test_get_query_templates_by_category(self):
        """Test filtering templates by category."""
        tag_templates = self.engine.get_query_templates(category="tag-analysis")
        workflow_templates = self.engine.get_query_templates(category="workflow")

        assert len(tag_templates) > 0
        assert len(workflow_templates) > 0

        # Verify filtering works
        for template in tag_templates:
            assert template.category == "tag-analysis"

        for template in workflow_templates:
            assert template.category == "workflow"

    def test_get_query_templates_by_complexity(self):
        """Test filtering templates by complexity."""
        basic_templates = self.engine.get_query_templates(complexity="basic")
        advanced_templates = self.engine.get_query_templates(complexity="advanced")

        assert len(basic_templates) > 0
        assert len(advanced_templates) > 0

        # Verify filtering works
        for template in basic_templates:
            assert template.complexity == "basic"

        for template in advanced_templates:
            assert template.complexity == "advanced"

    def test_get_optimization_suggestions(self):
        """Test query optimization suggestions."""
        # Test query with LIKE for text search (should suggest FTS)
        bad_query = "SELECT * FROM files WHERE content LIKE '%python%'"
        suggestions = self.engine.get_optimization_suggestions(bad_query)

        assert len(suggestions) > 0
        fts_suggestion = next((s for s in suggestions if 'fts' in s.suggestion.lower()), None)
        assert fts_suggestion is not None

        # Test query without LIMIT (should suggest adding LIMIT)
        no_limit_query = "SELECT * FROM files ORDER BY modified_date DESC"
        suggestions = self.engine.get_optimization_suggestions(no_limit_query)

        limit_suggestion = next((s for s in suggestions if 'limit' in s.suggestion.lower()), None)
        assert limit_suggestion is not None

    def test_template_structure(self):
        """Test that templates have required structure."""
        for template in self.engine.templates:
            assert isinstance(template, QueryTemplate)
            assert template.name
            assert template.description
            assert template.category
            assert template.sql_template
            assert isinstance(template.parameters, list)
            assert template.example_usage
            assert template.complexity in ['basic', 'intermediate', 'advanced']

            # Test parameters structure
            for param in template.parameters:
                assert isinstance(param, QueryParameter)
                assert param.name
                assert param.type
                assert param.description

    def test_optimization_structure(self):
        """Test that optimizations have required structure."""
        for optimization in self.engine.optimizations:
            assert isinstance(optimization, QueryOptimization)
            assert optimization.issue
            assert optimization.suggestion
            assert optimization.example_before
            assert optimization.example_after
            assert optimization.performance_impact in ['low', 'medium', 'high']

    def test_syntax_reference_structure(self):
        """Test that syntax reference has required structure."""
        syntax_ref = self.engine.syntax_reference

        assert 'tables' in syntax_ref
        assert 'operators' in syntax_ref
        assert 'functions' in syntax_ref
        assert 'fts_syntax' in syntax_ref

        # Test tables structure
        tables = syntax_ref['tables']
        expected_tables = ['files', 'tags', 'frontmatter', 'links', 'content_fts']
        for table in expected_tables:
            assert table in tables
            assert 'description' in tables[table]
            assert 'key_columns' in tables[table]

    def test_to_dict_serialization(self):
        """Test that the engine can be serialized to dict."""
        engine_dict = self.engine.to_dict()

        assert 'templates' in engine_dict
        assert 'optimizations' in engine_dict
        assert 'syntax_reference' in engine_dict
        assert 'common_patterns' in engine_dict

        # Test that it's JSON serializable
        json_str = json.dumps(engine_dict, default=str)
        assert len(json_str) > 0


class TestQueryTemplates:
    """Test specific query templates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QueryGuidanceEngine()

    def test_basic_tag_analysis_template(self):
        """Test the basic tag analysis template."""
        templates = self.engine.get_query_templates(category="tag-analysis", complexity="basic")
        basic_tag_template = next((t for t in templates if "Basic Tag Analysis" in t.name), None)

        assert basic_tag_template is not None
        assert "tag_list" in basic_tag_template.sql_template
        assert "limit" in basic_tag_template.sql_template

        # Check parameters
        param_names = [p.name for p in basic_tag_template.parameters]
        assert "tag_list" in param_names
        assert "limit" in param_names

    def test_hierarchical_tag_analysis_template(self):
        """Test the hierarchical tag analysis template."""
        templates = self.engine.get_query_templates(category="tag-analysis")
        hierarchical_template = next((t for t in templates if "Hierarchical" in t.name), None)

        assert hierarchical_template is not None
        assert "tag_pattern" in hierarchical_template.sql_template
        assert "WITH" in hierarchical_template.sql_template  # Uses CTE

    def test_workflow_analysis_template(self):
        """Test the development workflow analysis template."""
        templates = self.engine.get_query_templates(category="workflow")
        workflow_template = next((t for t in templates if "Development Workflow" in t.name), None)

        assert workflow_template is not None
        assert "workflow_tags" in workflow_template.sql_template
        assert "WITH" in workflow_template.sql_template  # Uses CTE

    def test_content_gap_analysis_template(self):
        """Test the content gap analysis template."""
        templates = self.engine.get_query_templates(category="content")
        gap_template = next((t for t in templates if "Gap Analysis" in t.name), None)

        assert gap_template is not None
        assert "topic_pattern" in gap_template.sql_template
        assert "days" in gap_template.sql_template
        assert "min_files" in gap_template.sql_template


class TestQueryOptimizations:
    """Test query optimization suggestions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QueryGuidanceEngine()

    def test_fts_optimization(self):
        """Test FTS optimization suggestion."""
        query = "SELECT * FROM files WHERE content LIKE '%python%'"
        suggestions = self.engine.get_optimization_suggestions(query)

        fts_suggestion = next((s for s in suggestions if 'fts' in s.suggestion.lower()), None)
        assert fts_suggestion is not None
        assert 'content_fts' in fts_suggestion.example_after
        assert fts_suggestion.performance_impact == 'high'

    def test_limit_optimization(self):
        """Test LIMIT optimization suggestion."""
        query = "SELECT * FROM files ORDER BY modified_date DESC"
        suggestions = self.engine.get_optimization_suggestions(query)

        limit_suggestion = next((s for s in suggestions if 'limit' in s.suggestion.lower()), None)
        assert limit_suggestion is not None
        assert 'LIMIT' in limit_suggestion.example_after

    def test_in_clause_optimization(self):
        """Test IN clause optimization suggestion."""
        query = "SELECT * FROM files f JOIN tags t ON f.id = t.file_id WHERE t.tag = 'ai' OR t.tag = 'llm' OR t.tag = 'coding'"
        suggestions = self.engine.get_optimization_suggestions(query)

        # Debug: print all suggestions
        print(f"Query: {query}")
        print(f"Suggestions: {[s.issue for s in suggestions]}")

        in_suggestion = next((s for s in suggestions if 'or conditions' in s.issue.lower()), None)
        assert in_suggestion is not None
        assert 'IN (' in in_suggestion.example_after

    def test_no_optimization_needed(self):
        """Test query that doesn't need optimization."""
        query = """SELECT f.filename, COUNT(t.tag) as tag_count
                   FROM files f
                   JOIN tags t ON f.id = t.file_id
                   WHERE t.tag IN ('ai', 'llm')
                   GROUP BY f.id
                   ORDER BY tag_count DESC
                   LIMIT 20"""

        suggestions = self.engine.get_optimization_suggestions(query)
        # This query is already well-optimized, so should have few or no suggestions
        assert len(suggestions) <= 1  # Maybe some minor suggestions, but not major ones


class TestExamples:
    """Test query examples."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = QueryGuidanceEngine()

    def test_tag_analysis_examples(self):
        """Test that tag analysis examples are relevant."""
        guidance = self.engine.get_query_guidance("tag-analysis")

        assert len(guidance.examples) > 0

        # Check that examples contain relevant content
        example_queries = [ex['query'] for ex in guidance.examples]
        tag_related = any('tag' in query.lower() for query in example_queries)
        assert tag_related

    def test_workflow_analysis_examples(self):
        """Test that workflow analysis examples are relevant."""
        guidance = self.engine.get_query_guidance("workflow")

        assert len(guidance.examples) > 0

        # Should include workflow-specific examples
        workflow_examples = [ex for ex in guidance.examples if 'workflow' in ex.get('title', '').lower()]
        assert len(workflow_examples) > 0

    def test_example_structure(self):
        """Test that examples have required structure."""
        guidance = self.engine.get_query_guidance("tag-analysis")

        for example in guidance.examples:
            assert 'title' in example
            assert 'description' in example
            assert 'query' in example
            assert len(example['query']) > 0
            assert 'SELECT' in example['query'].upper()


if __name__ == "__main__":
    pytest.main([__file__])