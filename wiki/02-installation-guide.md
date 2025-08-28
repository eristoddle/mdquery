# Installation Guide

## Minimum Setup Requirements

- Python 3.8+
- pip
- SQLite3 (bundled with Python)

## Installation Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd mdquery
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Package in Editable Mode

```bash
pip install -e .
```

This makes the `mdquery` command available in your terminal.

## Dependencies

The following dependencies are automatically installed:

- `python-frontmatter>=1.0.0` - For parsing YAML/TOML frontmatter
- `PyYAML>=6.0.0` - YAML processing
- `toml>=0.10.0` - TOML processing
- `click>=8.0.0` - Command-line interface
- `markdown>=3.4.0` - Markdown parsing
- `mcp>=1.0.0` - Model Communication Protocol support

## Development Dependencies

For development and testing:

- `pytest>=7.0.0` - Testing framework
- `black` - Code formatting
- `flake8` - Linting
- `mypy` - Type checking

Install development dependencies:

```bash
pip install -r requirements.txt
```

## Verification

Verify the installation by running:

```bash
mdquery --help
```

You should see the command-line help output.

## Optional Tools

- **pytest, black, flake8, mypy**: For development and testing
- **SQLite browser**: For database inspection (optional)

## Platform-Specific Notes

### Windows

No special requirements. Python 3.8+ includes SQLite3.

### macOS

No special requirements. Python 3.8+ includes SQLite3.

### Linux

Most distributions include SQLite3 with Python. If not:

```bash
# Ubuntu/Debian
sudo apt-get install sqlite3

# CentOS/RHEL
sudo yum install sqlite
```

## Troubleshooting

### Common Issues

1. **Python version too old**: Ensure Python 3.8 or higher
2. **Missing pip**: Install pip if not available
3. **Permission errors**: Use virtual environments or user installation

### Virtual Environment Recommended

```bash
python -m venv mdquery-env
source mdquery-env/bin/activate  # On Windows: mdquery-env\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Next Steps

After installation, see the [Quick Start Guide](02-quick-start-guide.md) to begin using mdquery.