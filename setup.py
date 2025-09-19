"""
Setup configuration for mdquery package.
"""

from setuptools import setup, find_packages
import os

# Read long description from README
def read_long_description():
    """Read the long description from README.md"""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "A SQL-like interface for searching and analyzing markdown files across different note-taking systems and static site generators."

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Filter out development dependencies
install_requires = [req for req in requirements if not any(
    dev_dep in req for dev_dep in ["pytest", "black", "flake8", "mypy"]
)]

setup(
    name="mdquery",
    version="0.3.0",
    description="Universal markdown querying tool with SQL-like syntax",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    author="mdquery",
    author_email="",
    url="https://github.com/yourusername/mdquery",  # Update with actual repository URL
    packages=find_packages(exclude=["tests", "tests.*"]),  # Exclude tests from distribution
    include_package_data=True,
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "mdquery=mdquery.cli:cli",
            "mdquery-mcp=mdquery.mcp:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup",
        "Topic :: Utilities",
    ],
    keywords="markdown, query, sql, search, obsidian, jekyll, static-site-generator",
)