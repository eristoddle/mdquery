#!/usr/bin/env python3
"""
Comprehensive test runner for mdquery.
Runs all test suites including format compatibility, performance, and end-to-end tests.
"""

import pytest
import sys
import os
from pathlib import Path
import subprocess
import time

def run_test_suite():
    """Run the comprehensive test suite."""

    print("=" * 60)
    print("mdquery Comprehensive Test Suite")
    print("=" * 60)

    # Ensure we're in the right directory
    test_dir = Path(__file__).parent
    os.chdir(test_dir.parent)

    # Test categories to run
    test_categories = [
        {
            'name': 'Unit Tests',
            'pattern': 'tests/test_*.py',
            'exclude': ['test_format_compatibility.py', 'test_performance.py', 'test_end_to_end.py'],
            'description': 'Core component unit tests'
        },
        {
            'name': 'Format Compatibility Tests',
            'pattern': 'tests/test_format_compatibility.py',
            'exclude': [],
            'description': 'Tests for Obsidian, Joplin, Jekyll, and generic markdown compatibility'
        },
        {
            'name': 'End-to-End Integration Tests',
            'pattern': 'tests/test_end_to_end.py',
            'exclude': [],
            'description': 'Complete workflow integration tests'
        },
        {
            'name': 'Performance Tests',
            'pattern': 'tests/test_performance.py',
            'exclude': [],
            'description': 'Performance tests with large file collections (requires test data)'
        }
    ]

    results = {}
    total_start_time = time.time()

    for category in test_categories:
        print(f"\n{'-' * 40}")
        print(f"Running: {category['name']}")
        print(f"Description: {category['description']}")
        print(f"{'-' * 40}")

        start_time = time.time()

        # Build pytest command
        cmd = ['python', '-m', 'pytest', category['pattern'], '-v']

        # Add exclusions if any
        for exclude in category['exclude']:
            cmd.extend(['--ignore', f"tests/{exclude}"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            end_time = time.time()

            results[category['name']] = {
                'success': result.returncode == 0,
                'duration': end_time - start_time,
                'output': result.stdout,
                'errors': result.stderr
            }

            if result.returncode == 0:
                print(f"✅ PASSED ({end_time - start_time:.1f}s)")
            else:
                print(f"❌ FAILED ({end_time - start_time:.1f}s)")
                print("STDOUT:", result.stdout[-500:])  # Last 500 chars
                print("STDERR:", result.stderr[-500:])  # Last 500 chars

        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT (>300s)")
            results[category['name']] = {
                'success': False,
                'duration': 300,
                'output': '',
                'errors': 'Test timed out after 300 seconds'
            }
        except Exception as e:
            print(f"💥 ERROR: {e}")
            results[category['name']] = {
                'success': False,
                'duration': 0,
                'output': '',
                'errors': str(e)
            }

    # Print summary
    total_duration = time.time() - total_start_time
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")

    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)

    for name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {name:<30} ({result['duration']:.1f}s)")

    print(f"\nOverall: {passed}/{total} test categories passed")
    print(f"Total time: {total_duration:.1f}s")

    # Return success if all categories passed
    return passed == total

def check_test_data():
    """Check if test data is available."""
    test_data_dir = Path(__file__).parent / "test_data"

    required_dirs = [
        "obsidian",
        "joplin",
        "jekyll",
        "generic",
        "edge_cases",
        "performance"
    ]

    missing = []
    for dir_name in required_dirs:
        dir_path = test_data_dir / dir_name
        if not dir_path.exists():
            missing.append(dir_name)
        elif dir_name == "performance":
            # Check if performance data has enough files
            md_files = list(dir_path.glob("*.md"))
            if len(md_files) < 100:
                missing.append(f"{dir_name} (insufficient files: {len(md_files)})")

    if missing:
        print("⚠️  Missing test data directories:")
        for m in missing:
            print(f"   - {m}")
        print("\nRun 'python tests/generate_performance_data.py' to generate performance test data.")
        print("Note: Performance test data is excluded from git (.gitignore) as it's large generated content.")
        return False

    return True

def main():
    """Main test runner."""
    print("Checking test data availability...")

    if not check_test_data():
        print("\n❌ Test data check failed. Some tests may be skipped.")
        print("Continuing with available tests...\n")
    else:
        print("✅ All test data available.\n")

    success = run_test_suite()

    if success:
        print("\n🎉 All test categories passed!")
        sys.exit(0)
    else:
        print("\n💥 Some test categories failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()