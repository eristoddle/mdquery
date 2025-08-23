# Development Guide

This section contains documentation for developers working on mdquery itself.

## Contents

- **[Contributing](contributing.md)** - How to contribute to mdquery
- **[Testing](testing.md)** - Running and writing tests
- **[Architecture](architecture.md)** - System design overview

## Quick Start for Contributors

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/mdquery.git
   cd mdquery
   ```

2. **Set up development environment**
   ```bash
   pip install -e .
   pip install -r requirements-dev.txt
   ```

3. **Run tests**
   ```bash
   pytest tests/
   ```

4. **Make your changes**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation as needed

5. **Submit a pull request**
   - Ensure all tests pass
   - Include clear description of changes
   - Reference any related issues

## Development Workflow

- Use feature branches for new development
- Write tests for all new functionality
- Follow PEP 8 coding standards
- Update documentation for user-facing changes
- Run the full test suite before submitting PRs

## Getting Help

- Check existing issues and discussions
- Ask questions in GitHub Discussions
- Review the architecture documentation for system understanding