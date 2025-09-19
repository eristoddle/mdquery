#!/bin/bash

# Quick release script for mdquery
# Usage: ./quick_release.sh [version] [--test] [--dry-run]

set -e

# Initialize pyenv if available
if command -v pyenv >/dev/null 2>&1; then
    eval "$(pyenv init -)"
    echo "🐍 Initialized pyenv (Python $(python --version 2>&1 | cut -d' ' -f2))"
fi

VERSION=""
TEST_FLAG=""
DRY_RUN=""

# Parse arguments
for arg in "$@"; do
    case $arg in
        --test)
            TEST_FLAG="--test-pypi"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        *)
            if [ -z "$VERSION" ]; then
                VERSION="$arg"
            fi
            shift
            ;;
    esac
done

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [--test] [--dry-run]"
    echo "Example: $0 0.2.0"
    echo "Example: $0 0.2.0 --test       # Upload to test PyPI"
    echo "Example: $0 0.2.0 --dry-run    # Preview changes only"
    echo "Example: $0 0.2.0 --test --dry-run  # Preview test release"
    exit 1
fi

if [ -n "$DRY_RUN" ]; then
    echo "🔍 Dry run mode - previewing release process for mdquery v$VERSION"
else
    echo "🚀 Starting release process for mdquery v$VERSION"
fi

# Run the Python release script
ARGS="$VERSION"
if [ -n "$TEST_FLAG" ]; then
    ARGS="$ARGS $TEST_FLAG"
    if [ -z "$DRY_RUN" ]; then
        echo "📦 Releasing to Test PyPI..."
    else
        echo "📦 Would release to Test PyPI..."
    fi
else
    if [ -z "$DRY_RUN" ]; then
        echo "📦 Releasing to PyPI..."
    else
        echo "📦 Would release to PyPI..."
    fi
fi

if [ -n "$DRY_RUN" ]; then
    ARGS="$ARGS $DRY_RUN"
fi

# Determine python command
if command -v pyenv >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD release.py $ARGS

if [ -z "$DRY_RUN" ]; then
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
    if [ -n "$TEST_FLAG" ]; then
        echo "  $0 $VERSION --test"
    else
        echo "  $0 $VERSION"
    fi
fi