#!/usr/bin/env fish

# Quick release script for mdquery (Fish shell version)
# Usage: ./quick_release.fish [version] [--test] [--dry-run]

set VERSION ""
set TEST_FLAG ""
set DRY_RUN ""

# Parse arguments
for arg in $argv
    switch $arg
        case --test
            set TEST_FLAG "--test-pypi"
        case --dry-run
            set DRY_RUN "--dry-run"
        case '*'
            if test -z "$VERSION"
                set VERSION $arg
            end
    end
end

if test -z "$VERSION"
    echo "Usage: "(status current-filename)" <version> [--test] [--dry-run]"
    echo "Example: "(status current-filename)" 0.2.0"
    echo "Example: "(status current-filename)" 0.2.0 --test       # Upload to test PyPI"
    echo "Example: "(status current-filename)" 0.2.0 --dry-run    # Preview changes only"
    echo "Example: "(status current-filename)" 0.2.0 --test --dry-run  # Preview test release"
    exit 1
end

# Initialize pyenv if available
if command -v pyenv >/dev/null 2>&1
    pyenv init - | source
    echo "🐍 Initialized pyenv (Python "(python --version 2>&1 | cut -d' ' -f2)")"
end

if test -n "$DRY_RUN"
    echo "🔍 Dry run mode - previewing release process for mdquery v$VERSION"
else
    echo "🚀 Starting release process for mdquery v$VERSION"
end

# Build arguments
set ARGS $VERSION
if test -n "$TEST_FLAG"
    set ARGS $ARGS $TEST_FLAG
    if test -z "$DRY_RUN"
        echo "📦 Releasing to Test PyPI..."
    else
        echo "📦 Would release to Test PyPI..."
    end
else
    if test -z "$DRY_RUN"
        echo "📦 Releasing to PyPI..."
    else
        echo "📦 Would release to PyPI..."
    end
end

if test -n "$DRY_RUN"
    set ARGS $ARGS $DRY_RUN
end

# Determine python command
if command -v pyenv >/dev/null 2>&1
    set PYTHON_CMD python
else
    set PYTHON_CMD python3
end

eval $PYTHON_CMD release.py $ARGS

if test -z "$DRY_RUN"
    echo "✅ Release complete!"
    echo ""
    echo "📋 Post-release checklist:"
    echo "  □ Verify package on PyPI: https://pypi.org/project/mdquery/"
    echo "  □ Test installation: pip install mdquery==$VERSION"
    echo "  □ Update documentation if needed"
    echo "  □ Announce the release"
else
    echo ""
    echo "📋 To actually perform the release, run without --dry-run:"
    if test -n "$TEST_FLAG"
        echo "  "(status current-filename)" $VERSION --test"
    else
        echo "  "(status current-filename)" $VERSION"
    end
end