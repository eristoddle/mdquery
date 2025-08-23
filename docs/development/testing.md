# Testing Guide

This guide covers running tests, writing new tests, and understanding the test architecture for mdquery.

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_query.py

# Run specific test function
pytest tests/test_query.py::test_basic_query

# Run tests matching a pattern
pytest -k "test_cache"
```

### Test Coverage

```bash
# Run tests with coverage report
pytest --cov=mdquery

# Generate HTML coverage report
pytest --cov=mdquery --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Performance Testing

```bash
# Run performance tests
pytest tests/test_performance.py

# Generate performance data
python tests/generate_performance_data.py

# Run comprehensive test suite
python tests/run_comprehensive_tests.py
```

## Test Structure

### Test Organization

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_data/                     # Test markdown files
├── test_*.py                      # Unit tests
├── test_*_integration.py          # Integration tests
├── test_end_to_end.py            # End-to-end tests
└── test_performance.py           # Performance tests
```

### Test Categories

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows
4. **Performance Tests**: Measure speed and resource usage

## Writing Tests

### Test Fixtures

Common fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)

@pytest.fixture
def sample_markdown_files(tmp_path):
    """Create sample markdown files for testing."""
    files = {
        'note1.md': '''---
title: Test Note 1
tags: [test, sample]
---

# Test Note 1

This is a test note with some content.
''',
        'note2.md': '''---
title: Test Note 2
tags: [test, example]
---

# Test Note 2

Another test note with [[note1]] link.
'''
    }

    for filename, content in files.items():
        (tmp_path / filename).write_text(content)

    return tmp_path
```

### Unit Test Example

```python
def test_query_engine_basic_query(temp_db, sample_markdown_files):
    """Test basic query execution."""
    # Setup
    cache_manager = CacheManager(temp_db)
    cache_manager.initialize_cache()

    indexer = Indexer(cache_manager=cache_manager)
    indexer.index_directory(sample_markdown_files)

    query_engine = QueryEngine(cache_manager=cache_manager)

    # Execute
    result = query_engine.execute_query("SELECT COUNT(*) as count FROM files")

    # Assert
    assert result.success
    assert len(result.data) == 1
    assert result.data[0]['count'] == 2
```

### Integration Test Example

```python
def test_indexer_query_integration(temp_db, sample_markdown_files):
    """Test indexer and query engine integration."""
    # Setup components
    cache_manager = CacheManager(temp_db)
    cache_manager.initialize_cache()

    indexer = Indexer(cache_manager=cache_manager)
    query_engine = QueryEngine(cache_manager=cache_manager)

    # Index files
    stats = indexer.index_directory(sample_markdown_files)
    assert stats['files_processed'] == 2

    # Query indexed data
    result = query_engine.execute_query("""
        SELECT f.filename, t.tag
        FROM files f
        JOIN tags t ON f.id = t.file_id
        WHERE t.tag = 'test'
    """)

    assert result.success
    assert len(result.data) == 2
```

### Testing Error Conditions

```python
def test_query_engine_invalid_sql(temp_db):
    """Test query engine handles invalid SQL gracefully."""
    cache_manager = CacheManager(temp_db)
    cache_manager.initialize_cache()

    query_engine = QueryEngine(cache_manager=cache_manager)

    # Test invalid SQL
    result = query_engine.execute_query("INVALID SQL QUERY")

    assert not result.success
    assert "syntax error" in result.error.lower()
```

### Testing Async Code (MCP Server)

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_mcp_server_query_tool():
    """Test MCP server query tool."""
    server = MDQueryMCPServer()

    # Mock database setup
    await server._ensure_initialized()

    # Test query tool
    result = await server.query_markdown("SELECT COUNT(*) FROM files")

    assert isinstance(result, str)
    data = json.loads(result)
    assert 'data' in data
```

## Test Data Management

### Creating Test Data

```python
def create_test_markdown_file(path: Path, title: str, content: str, **frontmatter):
    """Helper to create test markdown files."""
    fm_data = {'title': title, **frontmatter}
    fm_yaml = yaml.dump(fm_data, default_flow_style=False)

    full_content = f"---\n{fm_yaml}---\n\n{content}"
    path.write_text(full_content)
    return path
```

### Test Data Cleanup

```python
@pytest.fixture
def clean_test_db():
    """Ensure clean database state for each test."""
    db_path = "test.db"

    # Remove existing database
    if os.path.exists(db_path):
        os.unlink(db_path)

    yield db_path

    # Cleanup after test
    if os.path.exists(db_path):
        os.unlink(db_path)
```

## Mocking and Patching

### Mocking File System Operations

```python
from unittest.mock import patch, mock_open

def test_file_reading_with_mock():
    """Test file reading with mocked file system."""
    mock_content = "# Test\n\nMocked content"

    with patch('builtins.open', mock_open(read_data=mock_content)):
        # Test code that reads files
        result = some_function_that_reads_files()
        assert "Mocked content" in result
```

### Mocking Database Operations

```python
from unittest.mock import MagicMock

def test_query_with_mocked_db():
    """Test query execution with mocked database."""
    mock_db = MagicMock()
    mock_db.execute.return_value.fetchall.return_value = [
        {'id': 1, 'filename': 'test.md'}
    ]

    query_engine = QueryEngine(db_manager=mock_db)
    result = query_engine.execute_query("SELECT * FROM files")

    assert result.success
    assert len(result.data) == 1
```

## Performance Testing

### Benchmarking Queries

```python
import time

def test_query_performance(large_dataset):
    """Test query performance with large dataset."""
    query_engine = QueryEngine(cache_manager=large_dataset)

    start_time = time.time()
    result = query_engine.execute_query("SELECT * FROM files LIMIT 1000")
    execution_time = time.time() - start_time

    assert result.success
    assert execution_time < 1.0  # Should complete within 1 second
```

### Memory Usage Testing

```python
import psutil
import os

def test_memory_usage_during_indexing(large_directory):
    """Test memory usage during large directory indexing."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    indexer = Indexer()
    indexer.index_directory(large_directory)

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    # Memory increase should be reasonable (less than 100MB for test data)
    assert memory_increase < 100 * 1024 * 1024
```

## Continuous Integration

### GitHub Actions Configuration

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs (daily)

### Test Matrix

Tests run against:
- Python 3.8, 3.9, 3.10, 3.11
- Multiple operating systems (Ubuntu, macOS, Windows)
- Different SQLite versions

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with Python debugger
pytest --pdb tests/test_query.py::test_specific_function

# Run with verbose output and no capture
pytest -v -s tests/test_query.py

# Run single test with maximum verbosity
pytest -vvv tests/test_query.py::test_specific_function
```

### Logging in Tests

```python
import logging

def test_with_logging(caplog):
    """Test with log capture."""
    with caplog.at_level(logging.DEBUG):
        # Code that generates logs
        result = some_function()

    # Check logs
    assert "Expected log message" in caplog.text
    assert caplog.records[0].levelname == "DEBUG"
```

## Best Practices

### Test Naming

- Use descriptive names that explain what is being tested
- Follow pattern: `test_<component>_<scenario>_<expected_result>`
- Examples:
  - `test_query_engine_invalid_sql_returns_error`
  - `test_indexer_incremental_update_skips_unchanged_files`

### Test Organization

- Group related tests in the same file
- Use test classes for complex scenarios
- Keep tests independent and isolated
- Use fixtures for common setup

### Assertions

- Use specific assertions rather than generic ones
- Include helpful error messages
- Test both positive and negative cases
- Verify all important aspects of the result

### Test Data

- Use minimal test data that covers the scenario
- Make test data realistic but simple
- Clean up test data after tests
- Use fixtures for reusable test data

## Common Testing Patterns

### Testing Database Operations

```python
def test_database_transaction_rollback(temp_db):
    """Test database transaction rollback on error."""
    db_manager = DatabaseManager(temp_db)

    with pytest.raises(SomeExpectedException):
        with db_manager.transaction():
            # Operations that should be rolled back
            db_manager.execute("INSERT INTO files ...")
            raise SomeExpectedException("Simulated error")

    # Verify rollback occurred
    result = db_manager.execute("SELECT COUNT(*) FROM files")
    assert result.fetchone()[0] == 0
```

### Testing File Operations

```python
def test_file_processing_with_various_encodings(tmp_path):
    """Test file processing handles different encodings."""
    encodings = ['utf-8', 'latin-1', 'cp1252']

    for encoding in encodings:
        test_file = tmp_path / f"test_{encoding}.md"
        content = "# Test\n\nContent with special chars: àáâã"
        test_file.write_text(content, encoding=encoding)

        # Test processing
        result = process_file(test_file)
        assert result.success
        assert "special chars" in result.content
```

This testing guide should help you understand how to run tests, write new tests, and maintain test quality in the mdquery project.