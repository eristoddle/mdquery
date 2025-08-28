# Development Guide

## Testing Strategy

mdquery uses a comprehensive testing framework with multiple levels of coverage:

### Unit Testing
- **Individual component testing** with mocks and fixtures
- **90% code coverage minimum** requirement
- **Test examples**:
  ```python
  def test_frontmatter_extraction(self):
      content = "---\ntitle: Test\ntags: [test]\n---\n# Content"
      result = self.parser.parse(content)
      self.assertEqual(result['title'], 'Test')
  ```

### Integration Testing
- **Component interaction testing** with real database
- **End-to-end workflow validation**
- **Cache and performance integration**

### End-to-End Testing
- **Complete user workflow simulation**
- **Format compatibility testing** (Obsidian, Jekyll, Joplin)
- **Large dataset performance testing**

### Format Compatibility Testing
- **Obsidian**: Wikilinks, nested tags, callouts
- **Jekyll**: Frontmatter, post formats, categories
- **Joplin**: Inline metadata, resources
- **Generic**: Standard markdown features

### Performance Testing
- **Indexing performance**: 10+ files/second minimum
- **Query performance**: <5 seconds for complex queries
- **Memory usage**: Monitoring and optimization
- **Large repository testing**: 1000+ file repositories

### Error Handling Testing
- **Malformed file handling**
- **Database corruption recovery**
- **Memory exhaustion scenarios**
- **Encoding error handling**

## Contribution Guidelines

### Code Style Standards

#### PEP 8 Compliance
```python
def extract_frontmatter(content: str) -> Dict[str, Any]:
    """Extract frontmatter from markdown content.

    Args:
        content: Raw markdown content with potential frontmatter

    Returns:
        Dictionary containing frontmatter key-value pairs
    """
    if not content.startswith('---'):
        return {}

    frontmatter_end = content.find('\n---\n', 3)
    if frontmatter_end == -1:
        return {}

    return yaml.safe_load(content[3:frontmatter_end])
```

#### Type Hints Required
```python
def execute_query(
    self,
    sql: str,
    parameters: Optional[Tuple] = None,
    timeout: float = 30.0
) -> QueryResult:
    """Execute SQL query with optional parameters."""
    pass
```

#### Documentation Standards
All public functions require comprehensive docstrings with:
- Purpose description
- Parameters with types
- Return value description
- Usage examples
- Exception information

### Testing Requirements

#### Minimum Coverage
- **Unit tests**: 90% code coverage
- **Integration tests**: All public API methods
- **End-to-end tests**: Critical user workflows
- **Performance tests**: Resource-intensive operations

#### Test Organization
```
tests/
├── unit/              # Component isolation tests
├── integration/       # Component interaction tests
├── e2e/              # Complete workflow tests
├── performance/      # Performance benchmarks
└── compatibility/    # Format-specific tests
```

### Development Workflow

#### Setup Development Environment
```bash
# Clone repository
git clone <repository-url>
cd mdquery

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install testing and linting tools
pip install pytest black flake8 mypy
```

#### Code Quality Checks
```bash
# Format code
black mdquery/ tests/

# Lint code
flake8 mdquery/ tests/

# Type checking
mypy mdquery/

# Run tests
pytest tests/ -v --cov=mdquery --cov-report=html
```

#### Running Specific Tests
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v

# Specific test file
pytest tests/test_indexer.py -v

# Specific test method
pytest tests/test_indexer.py::TestIndexer::test_frontmatter_extraction -v
```

### Coding Standards and Best Practices

#### Architecture Principles
- **Separation of concerns**: Clear component boundaries
- **Dependency injection**: Use dependency injection for testability
- **Error handling**: Comprehensive exception handling
- **Performance**: Optimize for large datasets
- **Extensibility**: Support for new markdown formats

#### Security Considerations
- **SQL injection prevention**: Parameterized queries only
- **Input validation**: Validate all user inputs
- **File system safety**: Secure file operations
- **Resource limits**: Prevent resource exhaustion

#### Performance Guidelines
- **Database optimization**: Use appropriate indexes
- **Caching strategy**: Cache expensive operations
- **Memory management**: Efficient memory usage
- **Batch processing**: Process large datasets in chunks

### Pull Request Process

#### Before Submitting
1. **Code quality**: Pass all linting and type checks
2. **Tests**: Maintain 90%+ test coverage
3. **Documentation**: Update relevant documentation
4. **Performance**: No performance regressions
5. **Compatibility**: Test with all supported formats

#### PR Requirements
- **Clear description**: Explain changes and motivation
- **Test coverage**: Include appropriate tests
- **Breaking changes**: Document any breaking changes
- **Performance impact**: Note any performance implications

#### Review Process
1. **Automated checks**: CI/CD pipeline validation
2. **Code review**: Peer review for quality and design
3. **Testing**: Comprehensive testing validation
4. **Documentation**: Documentation completeness check

### Debugging and Performance Profiling

#### Debug Logging
```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('mdquery')

# Component-specific logging
logging.getLogger('mdquery.indexer').setLevel(logging.DEBUG)
logging.getLogger('mdquery.query').setLevel(logging.DEBUG)
```

#### Performance Profiling
```python
from mdquery.performance import PerformanceProfiler

# Profile query execution
profiler = PerformanceProfiler()
query_engine.set_profiler(profiler)

result = query_engine.execute_query(sql)
profile = profiler.get_profile()

print(f"Parse time: {profile.parse_time:.3f}s")
print(f"DB time: {profile.db_time:.3f}s")
print(f"Format time: {profile.format_time:.3f}s")
```

#### Memory Monitoring
```python
from mdquery.performance import MemoryMonitor

monitor = MemoryMonitor()
monitor.start()

# Perform operation
result = indexer.index_directory("/large/repository")

stats = monitor.stop()
print(f"Peak memory: {stats.peak_memory_mb:.1f} MB")
print(f"Memory delta: {stats.memory_delta_mb:.1f} MB")
```

## Release Process

### Version Management
- **Semantic versioning**: MAJOR.MINOR.PATCH
- **Release branches**: Feature branches for major releases
- **Hotfix process**: Critical bug fix process

### Quality Gates
1. **All tests pass**: Complete test suite validation
2. **Performance benchmarks**: No performance regressions
3. **Documentation**: Complete and up-to-date documentation
4. **Compatibility**: Backward compatibility maintained
5. **Security**: Security review completed

### Release Checklist
- [ ] Version number updated
- [ ] Changelog updated
- [ ] Documentation updated
- [ ] Performance benchmarks pass
- [ ] All tests pass
- [ ] Security review completed
- [ ] Release notes prepared