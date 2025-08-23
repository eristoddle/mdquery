# Test Data Collections

This directory contains test collections for different markdown formats and systems to ensure comprehensive compatibility testing.

## Structure

- `obsidian/` - Obsidian vault test data with wikilinks, tags, and Obsidian-specific features ✅ **Committed**
- `joplin/` - Joplin export test data with Joplin's markdown format ✅ **Committed**
- `jekyll/` - Jekyll site test data with frontmatter and liquid tags ✅ **Committed**
- `generic/` - Generic markdown files for standard markdown testing ✅ **Committed**
- `edge_cases/` - Edge cases and error conditions for robust testing ✅ **Committed**
- `performance/` - Large collection for performance testing (1000+ files) ❌ **Not Committed**

## Git Policy

### Committed Test Data
The small, curated test collections (obsidian, joplin, jekyll, generic, edge_cases) are committed to the repository because they:
- Are small in size (< 50 files total)
- Represent essential test cases for different markdown formats
- Are manually curated with specific test scenarios
- Are needed for CI/CD and development workflows

### Excluded Test Data
The `performance/` directory is excluded from git (.gitignore) because it:
- Contains 1000+ generated files (large repository bloat)
- Is automatically generated via `tests/generate_performance_data.py`
- Can be regenerated on any machine as needed
- Is only needed for performance testing, not regular development

## Usage

### For Regular Development
The committed test data is sufficient for most development and testing needs.

### For Performance Testing
Run the generator to create performance test data:
```bash
python tests/generate_performance_data.py
```

This creates the `performance/` directory with 1000+ test files for performance benchmarking.

### Running Tests
The test runner automatically checks for required test data and provides instructions if performance data is missing:
```bash
python tests/run_comprehensive_tests.py
```