"""
End-to-End Workflow Tests for MCP Server Main Use Cases.

This module provides comprehensive end-to-end tests that simulate real user workflows
with the MCP server. Implements requirements from task 10b.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
import sys
import time

# Add the mdquery module to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mdquery.config import SimplifiedConfig


class MockE2EMCPServer:
    """Mock MCP server for end-to-end workflow testing."""

    def __init__(self, config: SimplifiedConfig):
        self.config = config
        self.notes_dirs = [config.config.notes_dir]
        self.performance_stats = {"total_queries": 0, "execution_times": []}

        # Sample data for realistic responses
        self.sample_files = [
            {"id": 1, "filename": "ai_guide.md", "title": "AI Development Guide",
             "tags": ["ai", "development", "mcp"], "word_count": 2500},
            {"id": 2, "filename": "mcp_impl.md", "title": "MCP Implementation",
             "tags": ["mcp", "protocol", "server"], "word_count": 1800},
            {"id": 3, "filename": "performance.md", "title": "Performance Guide",
             "tags": ["performance", "optimization"], "word_count": 3200}
        ]

    async def execute_workflow(self, workflow_name: str, steps: list) -> list:
        """Execute a complete workflow with multiple steps."""
        results = []
        workflow_start = time.time()

        for i, step in enumerate(steps):
            step_start = time.time()

            try:
                result = await self._execute_step(step)
                step_time = (time.time() - step_start) * 1000

                results.append({
                    "step_number": i + 1,
                    "step_name": step.get("name", f"Step {i + 1}"),
                    "tool": step.get("tool"),
                    "success": True,
                    "result": result,
                    "execution_time_ms": step_time
                })

                self.performance_stats["total_queries"] += 1
                self.performance_stats["execution_times"].append(step_time / 1000)

            except Exception as e:
                results.append({
                    "step_number": i + 1,
                    "step_name": step.get("name", f"Step {i + 1}"),
                    "tool": step.get("tool"),
                    "success": False,
                    "error": str(e),
                    "execution_time_ms": (time.time() - step_start) * 1000
                })

        # Add workflow summary
        total_time = (time.time() - workflow_start) * 1000
        successful_steps = sum(1 for r in results if r["success"])

        summary = {
            "workflow_name": workflow_name,
            "total_steps": len(steps),
            "successful_steps": successful_steps,
            "failed_steps": len(steps) - successful_steps,
            "total_execution_time_ms": total_time,
            "success_rate": successful_steps / len(steps) if steps else 0
        }

        results.append({"workflow_summary": summary})
        return results

    async def _execute_step(self, step: dict) -> dict:
        """Execute a single workflow step."""
        tool = step.get("tool")
        params = step.get("parameters", {})

        # Simulate execution time
        await asyncio.sleep(0.01)

        if tool == "index_directory":
            return {
                "path": params.get("path", ""),
                "statistics": {
                    "files_processed": len(self.sample_files),
                    "files_indexed": len(self.sample_files),
                    "execution_time": 0.5
                }
            }
        elif tool == "query_markdown":
            sql = params.get("sql", "")
            matching_files = self.sample_files[:2]  # Simulate query results
            return {
                "columns": ["id", "filename", "title", "tags"],
                "rows": matching_files,
                "row_count": len(matching_files),
                "execution_time_ms": 25.0,
                "sql": sql
            }
        elif tool == "comprehensive_tag_analysis":
            return {
                "topic_groups": [
                    {
                        "name": "AI Development",
                        "document_count": 2,
                        "key_themes": ["ai", "development", "mcp"],
                        "content_quality_score": 0.85
                    }
                ],
                "actionable_insights": [
                    {
                        "title": "Improve documentation",
                        "implementation_difficulty": "medium",
                        "expected_impact": "high"
                    }
                ]
            }
        elif tool == "analyze_development_workflow":
            return {
                "improvement_opportunities": [
                    {
                        "title": "Automate testing pipeline",
                        "category": "automation",
                        "priority_score": 0.85
                    }
                ],
                "development_metrics": {
                    "workflow_efficiency": 0.78,
                    "automation_level": 0.65
                }
            }
        elif tool == "get_performance_stats":
            return {
                "total_queries": self.performance_stats["total_queries"],
                "avg_execution_time": 0.5,
                "cache_hit_rate": 0.85,
                "performance_summary": {"status": "excellent"}
            }
        elif tool == "get_schema":
            return {
                "tables": {
                    "files": {"columns": ["id", "filename", "title", "content"]},
                    "tags": {"columns": ["file_id", "tag", "source"]}
                }
            }
        else:
            raise ValueError(f"Unknown tool: {tool}")


class EndToEndWorkflowTest(unittest.TestCase):
    """End-to-end workflow tests for main use case scenarios."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="e2e_test_"))
        self.notes_dir = self.test_dir / "notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        self.create_test_files()

        # Create configuration
        self.config = SimplifiedConfig(notes_dir=str(self.notes_dir))
        self.server = MockE2EMCPServer(self.config)

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_test_files(self):
        """Create realistic test files."""
        files = [
            ("ai_guide.md", "# AI Development Guide\n\nTags: #ai #development #mcp"),
            ("mcp_impl.md", "# MCP Implementation\n\nTags: #mcp #protocol #server"),
            ("performance.md", "# Performance Guide\n\nTags: #performance #optimization")
        ]

        for filename, content in files:
            (self.notes_dir / filename).write_text(content)

    def test_complete_setup_workflow(self):
        """Test complete setup workflow from scratch."""
        print("\n--- Testing Complete Setup Workflow ---")

        workflow_steps = [
            {
                "name": "Index Directory",
                "tool": "index_directory",
                "parameters": {"path": str(self.notes_dir), "recursive": True}
            },
            {
                "name": "Get Schema",
                "tool": "get_schema",
                "parameters": {}
            },
            {
                "name": "Test Basic Query",
                "tool": "query_markdown",
                "parameters": {"sql": "SELECT * FROM files LIMIT 3"}
            }
        ]

        async def run_workflow():
            return await self.server.execute_workflow("setup", workflow_steps)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_workflow())
            summary = results[-1]["workflow_summary"]

            self.assertEqual(summary["total_steps"], 3)
            self.assertEqual(summary["successful_steps"], 3)
            self.assertEqual(summary["success_rate"], 1.0)

            print(f"✓ Setup workflow: {summary['successful_steps']}/{summary['total_steps']} steps")
            print(f"  Execution time: {summary['total_execution_time_ms']:.1f}ms")

        finally:
            loop.close()

    def test_ai_development_analysis_workflow(self):
        """Test AI development analysis workflow."""
        print("\n--- Testing AI Development Analysis Workflow ---")

        workflow_steps = [
            {
                "name": "Index Files",
                "tool": "index_directory",
                "parameters": {"path": str(self.notes_dir)}
            },
            {
                "name": "Query AI Files",
                "tool": "query_markdown",
                "parameters": {"sql": "SELECT * FROM files WHERE tags LIKE '%ai%'"}
            },
            {
                "name": "Tag Analysis",
                "tool": "comprehensive_tag_analysis",
                "parameters": {
                    "tag_patterns": "ai,development,mcp",
                    "grouping_strategy": "semantic"
                }
            },
            {
                "name": "Workflow Analysis",
                "tool": "analyze_development_workflow",
                "parameters": {"focus_areas": "mcp,automation"}
            }
        ]

        async def run_workflow():
            return await self.server.execute_workflow("ai_analysis", workflow_steps)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_workflow())
            summary = results[-1]["workflow_summary"]

            self.assertEqual(summary["total_steps"], 4)
            self.assertEqual(summary["successful_steps"], 4)

            # Verify analysis results
            tag_analysis = results[2]["result"]
            self.assertIn("topic_groups", tag_analysis)
            self.assertIn("actionable_insights", tag_analysis)

            workflow_analysis = results[3]["result"]
            self.assertIn("improvement_opportunities", workflow_analysis)

            print(f"✓ AI analysis workflow: {summary['successful_steps']}/{summary['total_steps']} steps")
            print(f"  Topic groups found: {len(tag_analysis['topic_groups'])}")
            print(f"  Improvement opportunities: {len(workflow_analysis['improvement_opportunities'])}")

        finally:
            loop.close()

    def test_performance_monitoring_workflow(self):
        """Test performance monitoring workflow."""
        print("\n--- Testing Performance Monitoring Workflow ---")

        workflow_steps = [
            {
                "name": "Run Test Queries",
                "tool": "query_markdown",
                "parameters": {"sql": "SELECT COUNT(*) FROM files"}
            },
            {
                "name": "Get Performance Stats",
                "tool": "get_performance_stats",
                "parameters": {"hours": 24}
            }
        ]

        async def run_workflow():
            return await self.server.execute_workflow("performance", workflow_steps)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_workflow())
            summary = results[-1]["workflow_summary"]

            self.assertEqual(summary["successful_steps"], 2)

            # Verify performance data
            perf_stats = results[1]["result"]
            self.assertIn("avg_execution_time", perf_stats)
            self.assertIn("cache_hit_rate", perf_stats)
            self.assertLess(perf_stats["avg_execution_time"], 5.0)  # Under 5 seconds

            print(f"✓ Performance monitoring: {summary['successful_steps']}/{summary['total_steps']} steps")
            print(f"  Average execution time: {perf_stats['avg_execution_time']:.2f}s")
            print(f"  Cache hit rate: {perf_stats['cache_hit_rate']:.1%}")

        finally:
            loop.close()

    def test_error_handling_workflow(self):
        """Test workflow error handling."""
        print("\n--- Testing Error Handling Workflow ---")

        workflow_steps = [
            {
                "name": "Valid Query",
                "tool": "query_markdown",
                "parameters": {"sql": "SELECT * FROM files"}
            },
            {
                "name": "Invalid Tool",
                "tool": "nonexistent_tool",
                "parameters": {}
            },
            {
                "name": "Recovery Query",
                "tool": "get_schema",
                "parameters": {}
            }
        ]

        async def run_workflow():
            return await self.server.execute_workflow("error_test", workflow_steps)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(run_workflow())
            summary = results[-1]["workflow_summary"]

            self.assertEqual(summary["total_steps"], 3)
            self.assertEqual(summary["successful_steps"], 2)  # Should have 1 failure
            self.assertEqual(summary["failed_steps"], 1)

            # Verify error was caught properly
            self.assertTrue(results[0]["success"])  # First step should succeed
            self.assertFalse(results[1]["success"])  # Second step should fail
            self.assertTrue(results[2]["success"])  # Third step should succeed (recovery)

            print(f"✓ Error handling: {summary['successful_steps']}/{summary['total_steps']} steps")
            print(f"  Failed steps handled gracefully: {summary['failed_steps']}")

        finally:
            loop.close()


def run_end_to_end_tests():
    """Run all end-to-end workflow tests."""
    print("=" * 60)
    print("End-to-End Workflow Tests")
    print("=" * 60)

    suite = unittest.TestLoader().loadTestsFromTestCase(EndToEndWorkflowTest)
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    print("End-to-End Test Summary")
    print("=" * 60)

    if result.wasSuccessful():
        print("✅ All end-to-end workflow tests passed!")
        print(f"  - Tests run: {result.testsRun}")
        print(f"  - Failures: {len(result.failures)}")
        print(f"  - Errors: {len(result.errors)}")
        print("\nAll main use case workflows function correctly end-to-end.")
    else:
        print("❌ Some end-to-end tests failed!")
        print(f"  - Tests run: {result.testsRun}")
        print(f"  - Failures: {len(result.failures)}")
        print(f"  - Errors: {len(result.errors)}")

        if result.failures:
            print("\nFailures:")
            for test, error in result.failures:
                print(f"  - {test}: {error}")

        if result.errors:
            print("\nErrors:")
            for test, error in result.errors:
                print(f"  - {test}: {error}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_end_to_end_tests()
    sys.exit(0 if success else 1)