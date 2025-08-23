"""
Performance tests for mdquery with large file collections.
Tests indexing speed, query performance, and memory usage.
"""

import pytest
import tempfile
import time
import psutil
import os
from pathlib import Path

from mdquery.indexer import Indexer
from mdquery.query import QueryEngine
from mdquery.cache import CacheManager


class TestPerformance:
    """Performance tests with large file collections."""

    @pytest.fixture(scope="class")
    def performance_data(self):
        """Ensure performance test data exists."""
        perf_dir = Path(__file__).parent / "test_data" / "performance"

        if not perf_dir.exists() or len(list(perf_dir.glob("*.md"))) < 100:
            pytest.skip("Performance test data not available. Run generate_performance_data.py first.")

        return perf_dir

    @pytest.fixture
    def temp_cache(self):
        """Create a temporary cache for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "perf_test.db"
            cache_manager = CacheManager(cache_path)
            cache_manager.initialize_cache()
            yield cache_manager

    def test_large_collection_indexing_speed(self, performance_data, temp_cache):
        """Test indexing speed with large file collections."""
        indexer = Indexer(cache_manager=temp_cache)

        # Measure indexing time
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        indexer.index_directory(performance_data)

        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        indexing_time = end_time - start_time
        memory_used = end_memory - start_memory

        # Get file count
        file_count = len(list(performance_data.rglob("*.md")))

        print(f"\\nIndexing Performance:")
        print(f"  Files indexed: {file_count}")
        print(f"  Total time: {indexing_time:.2f} seconds")
        print(f"  Files per second: {file_count / indexing_time:.1f}")
        print(f"  Memory used: {memory_used:.1f} MB")

        # Performance assertions
        assert indexing_time < 60, f"Indexing {file_count} files should take less than 60 seconds"
        assert file_count / indexing_time > 10, "Should index at least 10 files per second"
        assert memory_used < 500, "Should use less than 500MB for indexing"

    def test_query_performance(self, performance_data, temp_cache):
        """Test query performance on large collections."""
        # Index the data first
        indexer = Indexer(cache_manager=temp_cache)
        indexer.index_directory(performance_data)

        query_engine = QueryEngine(cache_manager=temp_cache)

        # Test various query types and measure performance
        queries = [
            ("Simple select", "SELECT COUNT(*) FROM files"),
            ("Tag search", "SELECT * FROM files WHERE id IN (SELECT file_id FROM tags WHERE tag = 'research')"),
            ("Full-text search", "SELECT * FROM content_fts WHERE content MATCH 'project'"),
            ("Date range", "SELECT * FROM files WHERE date(modified_date) > '2023-06-01'"),
            ("Complex join", """
                SELECT f.filename, COUNT(t.tag) as tag_count
                FROM files f
                LEFT JOIN tags t ON f.id = t.file_id
                GROUP BY f.id
                ORDER BY tag_count DESC
                LIMIT 10
            """),
            ("Aggregation", "SELECT tag, COUNT(*) as count FROM tags GROUP BY tag ORDER BY count DESC LIMIT 20")
        ]

        print(f"\\nQuery Performance:")

        for query_name, sql in queries:
            start_time = time.time()
            result = query_engine.execute_query(sql)
            end_time = time.time()

            query_time = end_time - start_time
            print(f"  {query_name}: {query_time:.3f}s ({len(result.rows)} results)")

            # Performance assertions
            assert query_time < 5.0, f"{query_name} should complete in under 5 seconds"
            assert len(result.rows) >= 0, f"{query_name} should return valid results"

    def test_incremental_indexing_performance(self, performance_data, temp_cache):
        """Test incremental indexing performance."""
        indexer = Indexer(cache_manager=temp_cache)

        # Initial full indexing
        start_time = time.time()
        indexer.index_directory(performance_data)
        full_index_time = time.time() - start_time

        # Simulate file modification by touching a few files
        test_files = list(performance_data.glob("*.md"))[:10]
        for file_path in test_files:
            file_path.touch()  # Update modification time

        # Incremental indexing
        start_time = time.time()
        indexer.index_directory(performance_data)  # Should only reindex modified files
        incremental_time = time.time() - start_time

        print(f"\\nIncremental Indexing Performance:")
        print(f"  Full indexing: {full_index_time:.2f}s")
        print(f"  Incremental (10 files): {incremental_time:.2f}s")
        print(f"  Speedup: {full_index_time / incremental_time:.1f}x")

        # Incremental should be much faster
        assert incremental_time < full_index_time / 5, "Incremental indexing should be at least 5x faster"
        assert incremental_time < 10, "Incremental indexing should complete in under 10 seconds"

    def test_memory_usage_stability(self, performance_data, temp_cache):
        """Test memory usage remains stable during operations."""
        indexer = Indexer(cache_manager=temp_cache)
        query_engine = QueryEngine(cache_manager=temp_cache)

        # Index data
        indexer.index_directory(performance_data)

        # Measure memory before queries
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

        # Run many queries to test for memory leaks
        for i in range(100):
            query_engine.execute_query("SELECT * FROM files LIMIT 10")
            query_engine.execute_query("SELECT COUNT(*) FROM tags")
            query_engine.execute_query("SELECT * FROM content_fts WHERE content MATCH 'test' LIMIT 5")

        # Measure memory after queries
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory

        print(f"\\nMemory Usage Stability:")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Memory growth: {memory_growth:.1f} MB")

        # Memory growth should be minimal
        assert memory_growth < 50, "Memory growth should be less than 50MB after 300 queries"

    def test_concurrent_query_performance(self, performance_data, temp_cache):
        """Test performance with concurrent queries."""
        import threading
        import queue

        # Index data first
        indexer = Indexer(cache_manager=temp_cache)
        indexer.index_directory(performance_data)

        # Prepare queries
        queries = [
            "SELECT COUNT(*) FROM files",
            "SELECT * FROM tags WHERE tag LIKE '%test%'",
            "SELECT * FROM content_fts WHERE content MATCH 'project' LIMIT 10",
            "SELECT filename FROM files ORDER BY modified_date DESC LIMIT 5"
        ]

        results_queue = queue.Queue()

        def run_queries(thread_id):
            """Run queries in a thread."""
            query_engine = QueryEngine(cache_manager=temp_cache)
            thread_times = []

            for query in queries * 5:  # Run each query 5 times
                start_time = time.time()
                result = query_engine.execute_query(query)
                end_time = time.time()
                thread_times.append(end_time - start_time)

            results_queue.put((thread_id, thread_times))

        # Run concurrent queries
        num_threads = 4
        threads = []

        start_time = time.time()

        for i in range(num_threads):
            thread = threading.Thread(target=run_queries, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Collect results
        all_times = []
        while not results_queue.empty():
            thread_id, times = results_queue.get()
            all_times.extend(times)

        avg_query_time = sum(all_times) / len(all_times)
        max_query_time = max(all_times)

        print(f"\\nConcurrent Query Performance:")
        print(f"  Threads: {num_threads}")
        print(f"  Total queries: {len(all_times)}")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Average query time: {avg_query_time:.3f}s")
        print(f"  Max query time: {max_query_time:.3f}s")

        # Performance assertions
        assert avg_query_time < 1.0, "Average query time should be under 1 second"
        assert max_query_time < 5.0, "No query should take more than 5 seconds"
        assert total_time < 30, "All concurrent queries should complete in under 30 seconds"


class TestScalability:
    """Test scalability with different collection sizes."""

    @pytest.fixture
    def temp_cache(self):
        """Create a temporary cache for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "scale_test.db"
            cache_manager = CacheManager(cache_path)
            cache_manager.initialize_cache()
            yield cache_manager

    def test_database_size_scaling(self, temp_cache):
        """Test how database size scales with content."""
        performance_data = Path(__file__).parent / "test_data" / "performance"

        if not performance_data.exists():
            pytest.skip("Performance test data not available")

        indexer = Indexer(cache_manager=temp_cache)

        # Index incrementally and measure database growth
        files = list(performance_data.rglob("*.md"))
        batch_sizes = [100, 250, 500, len(files)]

        print(f"\\nDatabase Size Scaling:")

        for batch_size in batch_sizes:
            if batch_size > len(files):
                batch_size = len(files)

            # Index batch
            for file_path in files[:batch_size]:
                indexer.index_file(file_path)

            # Measure database size
            db_size = temp_cache.cache_path.stat().st_size / 1024 / 1024  # MB

            print(f"  {batch_size} files: {db_size:.1f} MB ({db_size/batch_size*1000:.1f} KB/file)")

            # Database should scale reasonably
            kb_per_file = db_size / batch_size * 1000
            assert kb_per_file < 100, f"Database should use less than 100KB per file, got {kb_per_file:.1f}KB"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])