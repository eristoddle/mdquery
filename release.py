#!/usr/bin/env python3
"""
Automated PyPI Release Script for mdquery

This script automates the process of:
1. Updating version numbers in all relevant files
2. Committing and pushing changes to git
3. Building and uploading the package to PyPI using twine

Usage:
    python release.py [new_version]
    
Example:
    python release.py 0.2.0
"""

import os
import re
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=check, 
            capture_output=capture_output, 
            text=True
        )
        if capture_output and result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {cmd}")
        print(f"Error: {e}")
        if capture_output and e.stderr:
            print(f"Stderr: {e.stderr}")
        raise


def get_current_version():
    """Get the current version from __init__.py."""
    init_file = Path("mdquery/__init__.py")
    if not init_file.exists():
        raise FileNotFoundError("mdquery/__init__.py not found")
    
    content = init_file.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        raise ValueError("Could not find __version__ in mdquery/__init__.py")
    
    return match.group(1)


def update_version_in_file(file_path, old_version, new_version):
    """Update version in a specific file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"{file_path} not found")
    
    content = path.read_text()
    
    if file_path == "mdquery/__init__.py":
        # Update __version__ = "x.x.x"
        pattern = r'(__version__\s*=\s*["\'])([^"\']+)(["\'])'
        replacement = f'\\g<1>{new_version}\\g<3>'
    elif file_path == "setup.py":
        # Update version="x.x.x",
        pattern = r'(version\s*=\s*["\'])([^"\']+)(["\'])'
        replacement = f'\\g<1>{new_version}\\g<3>'
    else:
        raise ValueError(f"Don't know how to update version in {file_path}")
    
    new_content = re.sub(pattern, replacement, content)
    
    if new_content == content:
        print(f"Warning: No version update made in {file_path}")
        return False
    
    path.write_text(new_content)
    print(f"Updated version in {file_path}: {old_version} -> {new_version}")
    return True


def validate_version_format(version):
    """Validate that version follows semantic versioning format."""
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9\-\.]+)?(?:\+[a-zA-Z0-9\-\.]+)?$'
    if not re.match(pattern, version):
        raise ValueError(f"Invalid version format: {version}. Expected format: X.Y.Z")


def check_git_status(dry_run=False):
    """Check if git working directory is clean."""
    result = run_command("git status --porcelain")
    if result.stdout.strip():
        print("Warning: Git working directory is not clean.")
        print("Uncommitted changes:")
        print(result.stdout)
        if dry_run:
            print("(Dry run mode - would prompt to continue)")
            return
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborting release.")
            sys.exit(1)


def check_dependencies(dry_run=False):
    """Check if required tools are available."""
    # Check for git
    try:
        run_command("which git")
    except subprocess.CalledProcessError:
        print("git is required but not found. Please install git.")
        sys.exit(1)
    
    # Check for python3
    try:
        run_command("which python3")
    except subprocess.CalledProcessError:
        print("python3 is required but not found. Please install Python 3.")
        sys.exit(1)
    
    # Only check twine if not doing a dry run
    if not dry_run:
        try:
            run_command("which twine")
        except subprocess.CalledProcessError:
            print("twine is required but not found. Install it with: pip install twine")
            sys.exit(1)
        
        # Check if twine is available in Python
        try:
            run_command("python3 -c 'import twine'")
        except subprocess.CalledProcessError:
            print("twine is not installed. Install it with: pip install twine")
            sys.exit(1)


def clean_build_artifacts():
    """Clean up any existing build artifacts."""
    artifacts = ['build', 'dist', 'mdquery.egg-info']
    for artifact in artifacts:
        if Path(artifact).exists():
            print(f"Removing {artifact}")
            run_command(f"rm -rf {artifact}")


def build_package():
    """Build the package for distribution."""
    print("Building package...")
    run_command("python3 setup.py sdist bdist_wheel")


def upload_to_pypi(test_pypi=False):
    """Upload package to PyPI (or test PyPI)."""
    if test_pypi:
        repository_url = "--repository testpypi"
        print("Uploading to Test PyPI...")
    else:
        repository_url = ""
        print("Uploading to PyPI...")
    
    run_command(f"twine upload {repository_url} dist/*")


def main():
    parser = argparse.ArgumentParser(description="Automated PyPI release script for mdquery")
    parser.add_argument("version", help="New version number (e.g., 0.2.0)")
    parser.add_argument("--test-pypi", action="store_true", 
                       help="Upload to Test PyPI instead of PyPI")
    parser.add_argument("--skip-git", action="store_true", 
                       help="Skip git operations (commit and push)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without actually doing it")
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    
    # Validate inputs
    validate_version_format(args.version)
    new_version = args.version
    
    # Check dependencies
    check_dependencies(dry_run=args.dry_run)
    
    # Get current version
    try:
        current_version = get_current_version()
        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")
    except Exception as e:
        print(f"Error getting current version: {e}")
        sys.exit(1)
    
    if current_version == new_version:
        print("New version is the same as current version. Nothing to do.")
        sys.exit(0)
    
    # Check git status
    if not args.skip_git:
        check_git_status(dry_run=args.dry_run)
    
    try:
        # Update version in files
        files_to_update = [
            "mdquery/__init__.py",
            "setup.py"
        ]
        
        if not args.dry_run:
            for file_path in files_to_update:
                update_version_in_file(file_path, current_version, new_version)
        else:
            print(f"Would update version in: {', '.join(files_to_update)}")
        
        # Git operations
        if not args.skip_git and not args.dry_run:
            print("Committing changes...")
            run_command(f"git add {' '.join(files_to_update)}")
            run_command(f'git commit -m "Bump version to {new_version}"')
            
            print("Pushing to remote...")
            run_command("git push")
            
            print("Creating git tag...")
            run_command(f"git tag v{new_version}")
            run_command("git push --tags")
        elif not args.skip_git:
            print("Would commit and push changes, create tag")
        
        # Clean and build
        if not args.dry_run:
            clean_build_artifacts()
            build_package()
        else:
            print("Would clean build artifacts and build package")
        
        # Upload to PyPI
        if not args.dry_run:
            upload_to_pypi(test_pypi=args.test_pypi)
        else:
            target = "Test PyPI" if args.test_pypi else "PyPI"
            print(f"Would upload to {target}")
        
        print(f"✅ Successfully released mdquery {new_version}!")
        
        if not args.dry_run:
            print("\nNext steps:")
            print("1. Verify the package is available on PyPI")
            print("2. Test installation: pip install mdquery")
            print("3. Update documentation if needed")
        
    except Exception as e:
        print(f"❌ Release failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()