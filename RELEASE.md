# PyPI Release Configuration for mdquery

## Prerequisites

1. **Required Tools:**
   - Python 3.8+
   - Git
   - twine (`pip install twine`)
   - setuptools and wheel (`pip install setuptools wheel`)

2. **PyPI Account Setup:**
   - Create account on https://pypi.org/
   - Create account on https://test.pypi.org/ (for testing)
   - Generate API tokens for authentication

3. **Authentication Setup:**
   Create ~/.pypirc file with your credentials:
   ```ini
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   username = __token__
   password = pypi-your-api-token-here

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-your-test-api-token-here
   ```

## Release Process

### Automated Release (Recommended)

1. **Preview Release (Dry Run):**
   ```bash
   # Preview what would happen for Test PyPI
   ./quick_release.sh 0.2.0 --test --dry-run
   
   # Preview what would happen for production PyPI
   ./quick_release.sh 0.2.0 --dry-run
   ```

2. **Test Release:**
   ```bash
   # Test on Test PyPI first
   ./quick_release.sh 0.2.0 --test
   ```

3. **Production Release:**
   ```bash
   # Release to PyPI
   ./quick_release.sh 0.2.0
   ```

### Manual Release

1. **Update Version:**
   ```bash
   python release.py 0.2.0 --dry-run  # Preview changes
   python release.py 0.2.0            # Execute release
   ```

2. **Advanced Options:**
   ```bash
   # Skip git operations
   python release.py 0.2.0 --skip-git
   
   # Release to test PyPI
   python release.py 0.2.0 --test-pypi
   ```

## Version Files

The following files contain version information and are automatically updated:
- `mdquery/__init__.py` - Package version
- `setup.py` - Setup configuration version

## Build Artifacts

The release script will create:
- `dist/` - Distribution files (.tar.gz and .whl)
- `build/` - Build artifacts
- `mdquery.egg-info/` - Package metadata

These are automatically cleaned before each build.

## Post-Release Checklist

- [ ] Verify package appears on PyPI
- [ ] Test installation: `pip install mdquery==X.Y.Z`
- [ ] Verify console scripts work: `mdquery --help`
- [ ] Test import: `python -c "import mdquery; print(mdquery.__version__)"`
- [ ] Update documentation if needed
- [ ] Announce release (if applicable)

## Troubleshooting

### Common Issues

1. **Authentication Errors:**
   - Verify ~/.pypirc is configured correctly
   - Check API tokens are valid
   - Ensure username is `__token__` when using API tokens

2. **Version Already Exists:**
   - PyPI doesn't allow re-uploading the same version
   - Increment version number and try again

3. **Build Failures:**
   - Check setup.py configuration
   - Verify all dependencies are available
   - Clean build artifacts: `rm -rf build dist *.egg-info`

4. **Git Issues:**
   - Ensure working directory is clean
   - Check git credentials are configured
   - Verify you have push access to the repository

### Manual Commands

If the automated script fails, you can run commands manually:

```bash
# Clean previous builds
rm -rf build dist mdquery.egg-info

# Build package
python setup.py sdist bdist_wheel

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```