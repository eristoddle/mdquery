#!/usr/bin/env python3
"""
Entry point for mdquery MCP server.

This module provides a simple command-line interface for starting
the mdquery MCP server.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import mdquery
sys.path.insert(0, str(Path(__file__).parent.parent))

from mdquery.mcp import main

if __name__ == "__main__":
    main()