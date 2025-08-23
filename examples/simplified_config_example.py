#!/usr/bin/env python3
"""
Example demonstrating the simplified configuration system for mdquery MCP server.

This example shows how to use the new SimplifiedConfig class to set up
mdquery with just a notes directory path, with automatic directory creation
and intelligent defaults.
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mdquery.config import SimplifiedConfig, create_helpful_error_message
from mdquery.mcp import MDQueryMCPServer
from mdquery.exceptions import ConfigurationError, MdqueryError


def create_example_vault(base_dir: Path) -> Path:
    """Create an example Obsidian vault with some test content."""
    vault_dir = base_dir / "example_vault"
    vault_dir.mkdir(exist_ok=True)

    # Create Obsidian vault structure
    (vault_dir / ".obsidian").mkdir(exist_ok=True)

    # Create some example notes
    daily_notes = vault_dir / "Daily Notes"
    daily_notes.mkdir(exist_ok=True)

    projects = vault_dir / "Projects"
    projects.mkdir(exist_ok=True)

    # Create example content
    (daily_notes / "2024-01-01.md").write_text("""---
tags: [daily, planning]
date: 2024-01-01
---

# Daily Note - January 1, 2024

## Tasks
- [ ] Review project status
- [ ] Plan Q1 objectives
- [x] Set up mdquery MCP server

## Notes
- Working on [[Projects/MCP Workflow Optimization]]
- Need to improve development workflow

## Links
- [[Projects/AI Development Process]]
""")

    (projects / "MCP Workflow Optimization.md").write_text("""---
tags: [project, mcp, workflow, ai-development]
status: active
priority: high
---

# MCP Workflow Optimization

## Overview
Optimizing mdquery's MCP server implementation to support streamlined AI development workflows.

## Goals
- Simplify configuration to require only notes directory path
- Enable comprehensive tag-based analysis
- Improve AI assistant integration

## Progress
- [x] Design simplified configuration system
- [ ] Implement comprehensive tag analysis
- [ ] Add workflow analysis engine

## Related Notes
- [[AI Development Process]]
- [[Daily Notes/2024-01-01]]
""")

    (projects / "AI Development Process.md").write_text("""---
tags: [ai, development, process, automation]
category: methodology
---

# AI Development Process

## Current Workflow
1. Research and planning in Obsidian
2. Code development with AI assistance
3. Testing and iteration
4. Documentation updates

## Pain Points
- Manual query construction for analysis
- Difficulty finding related content
- No automated workflow insights

## Improvements Needed
- Automated content analysis
- Better tag-based organization
- Workflow pattern detection

## Tools
- Obsidian for note-taking
- mdquery for content analysis
- AI assistants for development
""")

    print(f"✅ Created example vault at: {vault_dir}")
    return vault_dir


def demonstrate_basic_configuration():
    """Demonstrate basic SimplifiedConfig usage."""
    print("\n" + "="*60)
    print("BASIC CONFIGURATION EXAMPLE")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create example vault
        vault_dir = create_example_vault(temp_path)

        try:
            # Create simplified configuration with just the notes directory
            print(f"\n📁 Creating configuration for: {vault_dir}")
            config = SimplifiedConfig(notes_dir=vault_dir)

            print(f"✅ Configuration created successfully!")
            print(f"   Notes directory: {config.config.notes_dir}")
            print(f"   Database path: {config.config.db_path}")
            print(f"   Cache directory: {config.config.cache_dir}")
            print(f"   Note system type: {config.config.note_system_type.value}")
            print(f"   Auto-indexing: {config.config.auto_index}")

            # Show that directories were created
            print(f"\n📂 Directory structure created:")
            mdquery_dir = vault_dir / ".mdquery"
            if mdquery_dir.exists():
                print(f"   ✅ {mdquery_dir}")
                for item in mdquery_dir.iterdir():
                    print(f"      ├── {item.name}")

            return config

        except (ConfigurationError, MdqueryError) as e:
            error_message = create_helpful_error_message(e, str(vault_dir))
            print(f"❌ Configuration failed:\n{error_message}")
            return None


def demonstrate_custom_paths():
    """Demonstrate configuration with custom database and cache paths."""
    print("\n" + "="*60)
    print("CUSTOM PATHS EXAMPLE")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create example vault
        vault_dir = create_example_vault(temp_path)

        # Create custom locations
        custom_db = temp_path / "custom_db" / "my_database.db"
        custom_cache = temp_path / "custom_cache"

        try:
            print(f"\n📁 Creating configuration with custom paths:")
            print(f"   Notes: {vault_dir}")
            print(f"   Database: {custom_db}")
            print(f"   Cache: {custom_cache}")

            config = SimplifiedConfig(
                notes_dir=vault_dir,
                db_path=custom_db,
                cache_dir=custom_cache,
                auto_index=False  # Disable auto-indexing for this example
            )

            print(f"✅ Configuration created successfully!")
            print(f"   Auto-indexing disabled: {not config.config.auto_index}")

            # Verify custom directories were created
            print(f"\n📂 Custom directories created:")
            if custom_db.parent.exists():
                print(f"   ✅ Database directory: {custom_db.parent}")
            if custom_cache.exists():
                print(f"   ✅ Cache directory: {custom_cache}")

            return config

        except (ConfigurationError, MdqueryError) as e:
            error_message = create_helpful_error_message(e, str(vault_dir))
            print(f"❌ Configuration failed:\n{error_message}")
            return None


def demonstrate_mcp_server_integration(config: SimplifiedConfig):
    """Demonstrate MCP server initialization with SimplifiedConfig."""
    print("\n" + "="*60)
    print("MCP SERVER INTEGRATION EXAMPLE")
    print("="*60)

    try:
        print(f"\n🚀 Initializing MCP server with configuration...")
        server = MDQueryMCPServer(config=config)

        print(f"✅ MCP server created successfully!")
        print(f"   Server database path: {server.db_path}")
        print(f"   Server cache directory: {server.cache_dir}")
        print(f"   Notes directories: {server.notes_dirs}")
        print(f"   Auto-indexing enabled: {server.auto_index}")

        # Show configuration serialization
        print(f"\n📋 Configuration as dictionary:")
        config_dict = config.get_mcp_config()
        for key, value in config_dict.items():
            print(f"   {key}: {value}")

        return server

    except Exception as e:
        print(f"❌ MCP server initialization failed: {e}")
        return None


def demonstrate_configuration_persistence():
    """Demonstrate saving and loading configuration."""
    print("\n" + "="*60)
    print("CONFIGURATION PERSISTENCE EXAMPLE")
    print("="*60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create example vault
        vault_dir = create_example_vault(temp_path)

        try:
            # Create and save configuration
            print(f"\n💾 Creating and saving configuration...")
            original_config = SimplifiedConfig(notes_dir=vault_dir, auto_index=False)
            original_config.save_config()

            config_file = vault_dir / ".mdquery" / "config.json"
            print(f"   Configuration saved to: {config_file}")

            # Load configuration
            print(f"\n📖 Loading configuration from file...")
            loaded_config = SimplifiedConfig.load_config(config_file)

            print(f"✅ Configuration loaded successfully!")
            print(f"   Original auto-index: {original_config.config.auto_index}")
            print(f"   Loaded auto-index: {loaded_config.config.auto_index}")
            print(f"   Paths match: {original_config.config.notes_dir == loaded_config.config.notes_dir}")

            # Show config file content
            print(f"\n📄 Configuration file content:")
            with open(config_file, 'r') as f:
                import json
                config_data = json.load(f)
                print(json.dumps(config_data, indent=2))

        except (ConfigurationError, MdqueryError) as e:
            error_message = create_helpful_error_message(e, str(vault_dir))
            print(f"❌ Configuration persistence failed:\n{error_message}")


def demonstrate_error_handling():
    """Demonstrate helpful error messages for common configuration issues."""
    print("\n" + "="*60)
    print("ERROR HANDLING EXAMPLES")
    print("="*60)

    # Test 1: Nonexistent directory
    print(f"\n🔍 Testing nonexistent directory error...")
    try:
        SimplifiedConfig(notes_dir="/path/that/does/not/exist")
    except (ConfigurationError, MdqueryError) as e:
        error_message = create_helpful_error_message(e, "/path/that/does/not/exist")
        print(f"Expected error caught:\n{error_message}")

    # Test 2: Empty path
    print(f"\n🔍 Testing empty path error...")
    try:
        SimplifiedConfig(notes_dir="")
    except (ConfigurationError, MdqueryError) as e:
        error_message = create_helpful_error_message(e, "")
        print(f"Expected error caught:\n{error_message}")

    # Test 3: File instead of directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "not_a_directory.txt"
        test_file.write_text("This is a file, not a directory")

        print(f"\n🔍 Testing file-instead-of-directory error...")
        try:
            SimplifiedConfig(notes_dir=test_file)
        except (ConfigurationError, MdqueryError) as e:
            error_message = create_helpful_error_message(e, str(test_file))
            print(f"Expected error caught:\n{error_message}")


def main():
    """Run all configuration examples."""
    print("🎯 mdquery Simplified Configuration Examples")
    print("=" * 60)
    print("This script demonstrates the new simplified configuration system")
    print("that requires only a notes directory path with intelligent defaults.")

    # Run examples
    config1 = demonstrate_basic_configuration()
    config2 = demonstrate_custom_paths()

    if config1:
        demonstrate_mcp_server_integration(config1)

    demonstrate_configuration_persistence()
    demonstrate_error_handling()

    print("\n" + "="*60)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*60)
    print("\nKey benefits of the simplified configuration system:")
    print("• Only requires notes directory path")
    print("• Automatic .mdquery directory creation")
    print("• Intelligent note system detection (Obsidian, Joplin, etc.)")
    print("• Comprehensive error handling with helpful messages")
    print("• Configuration persistence and loading")
    print("• Backward compatibility with legacy configuration")


if __name__ == "__main__":
    main()