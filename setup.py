"""
Setup configuration for mdquery package.
"""

from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Filter out development dependencies
install_requires = [req for req in requirements if not any(
    dev_dep in req for dev_dep in ["pytest", "black", "flake8", "mypy"]
)]

setup(
    name="mdquery",
    version="0.2.0",
    description="Universal markdown querying tool with SQL-like syntax",
    long_description="A SQL-like interface for searching and analyzing markdown files across different note-taking systems and static site generators.",
    author="mdquery",
    packages=find_packages(),
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
    ],
)