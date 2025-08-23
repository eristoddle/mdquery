# Contributing to mdquery

Thank you for your interest in contributing to mdquery! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- SQLite 3

### Environment Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/mdquery.git
   cd mdquery
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. **Verify installation**
   ```bash
   mdquery --version
   pytest tests/ -v
   ```

## Code Standards

### Python Style

- Follow PEP 8 coding standards
- Use type hints for all function parameters and return values
- Maximum line length: 100 characters
- Use descriptive variable and function names

### Documentation

- All public functions and classes must have docstrings
- Use Google-style docstrings
- Include examples in docstrings where helpful
- Update user documentation for new features

### Testing

- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names that explain what is being tested
- Include both unit tests and integration tests

## Contribution Process

### 1. Choose an Issue

- Look for issues labeled "good first issue" for beginners
- Comment on the issue to indicate you're working on it
- Ask questions if the requirements are unclear

### 2. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 3. Make Your Changes

- Write clean, well-documented code
- Add or update tests as needed
- Update documentation if necessary
- Follow the existing code patterns and style

### 4. Test Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_your_feature.py

# Run with coverage
pytest tests/ --cov=mdquery --cov-report=html
```

### 5. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "Add fuzzy search functionality for content discovery

- Implement fuzzy matching algorithm using difflib
- Add threshold parameter for similarity scoring
- Include tests for various similarity scenarios
- Update documentation with usage examples"
```

### 6. Submit a Pull Request

1. Push your branch to your fork
2. Create a pull request on GitHub
3. Fill out the PR template completely
4. Link to any related issues
5. Wait for review and address feedback

## Types of Contributions

### Bug Fixes

- Include steps to reproduce the bug
- Add a test that would have caught the bug
- Explain the root cause in your PR description

### New Features

- Discuss the feature in an issue first
- Consider backward compatibility
- Add comprehensive tests
- Update documentation and examples

### Documentation

- Fix typos and improve clarity
- Add missing documentation
- Update examples to reflect current API
- Improve code comments

### Performance Improvements

- Include benchmarks showing the improvement
- Ensure the change doesn't break existing functionality
- Consider memory usage as well as speed

## Code Review Process

### What Reviewers Look For

- Code correctness and functionality
- Test coverage and quality
- Documentation completeness
- Performance implications
- Security considerations
- Backward compatibility

### Addressing Feedback

- Respond to all review comments
- Make requested changes promptly
- Ask for clarification if feedback is unclear
- Update your PR description if the scope changes

## Release Process

### Version Numbering

We follow semantic versioning (SemVer):
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

### Changelog

- All user-facing changes should be documented
- Include migration notes for breaking changes
- Credit contributors in release notes

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Pull Request Comments**: Code-specific discussions

### Resources

- [Architecture Documentation](architecture.md)
- [Testing Guide](testing.md)
- [API Reference](../api/README.md)
- [User Guide](../user-guide/README.md)

## Recognition

Contributors are recognized in:
- Release notes
- Contributors section of README
- GitHub contributor graphs

Thank you for helping make mdquery better!