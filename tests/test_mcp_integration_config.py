"""
Integration tests for MCP server with simplified configuration.

This module tests the integration between SimplifiedConfig and MDQueryMCPServer
to ensure proper initialization and functionality.
"""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mdquery.config import SimplifiedConfig
from mdquery.mcp import MDQueryMCPServer


class TestMCPServerIntegration:
    """Test cases for MCP server integration with SimplifiedConfig."""

    def test_mcp_server_with_simplified_config(self, tmp_path):
        """Test MCP server initialization with SimplifiedConfig."""
        # Create test notes directory with some markdown files
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create a simple markdown file
        test_file = notes_dir / "test.md"
        test_file.write_text("# Test Note\n\nThis is a test note.")

        # Create simplified configuration
        config = SimplifiedConfig(notes_dir=notes_dir)

        # Initialize MCP server with configuration
        server = MDQueryMCPServer(config=config)

        # Verify server properties
        assert server.config == config
        assert server.db_path == config.config.db_path
        assert server.cache_dir == config.config.cache_dir
        assert server.notes_dirs == [config.config.notes_dir]
        assert server.auto_index == config.config.auto_index

    def test_mcp_server_legacy_initialization(self, tmp_path):
        """Test MCP server with legacy initialization for backward compatibility."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        db_path = tmp_path / "custom.db"
        cache_dir = tmp_path / "cache"

        # Initialize MCP server with legacy parameters
        server = MDQueryMCPServer(
            db_path=db_path,
            cache_dir=cache_dir,
            notes_dirs=[notes_dir]
        )

        # Verify server properties
        assert server.config is None  # No SimplifiedConfig used
        assert server.db_path == db_path
        assert server.cache_dir == cache_dir
        assert server.notes_dirs == [notes_dir]
        assert server.auto_index is True  # Default value

    def test_mcp_server_auto_indexing_enabled(self, tmp_path):
        """Test that auto-indexing is properly configured."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create markdown files
        (notes_dir / "note1.md").write_text("# Note 1\n\nContent 1")
        (notes_dir / "note2.md").write_text("# Note 2\n\nContent 2")

        # Create configuration with auto-indexing enabled
        config = SimplifiedConfig(notes_dir=notes_dir, auto_index=True)
        server = MDQueryMCPServer(config=config)

        assert server.auto_index is True

    def test_mcp_server_auto_indexing_disabled(self, tmp_path):
        """Test that auto-indexing can be disabled."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create configuration with auto-indexing disabled
        config = SimplifiedConfig(notes_dir=notes_dir, auto_index=False)
        server = MDQueryMCPServer(config=config)

        assert server.auto_index is False

    def test_mcp_server_directory_structure_creation(self, tmp_path):
        """Test that MCP server works with automatically created directories."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create configuration (this should create .mdquery directories)
        config = SimplifiedConfig(notes_dir=notes_dir)

        # Verify directories were created
        assert (notes_dir / ".mdquery").exists()
        assert (notes_dir / ".mdquery" / "cache").exists()
        assert config.config.db_path.parent.exists()

        # Initialize MCP server
        server = MDQueryMCPServer(config=config)

        # Verify server can access the directories
        assert server.db_path.parent.exists()
        assert server.cache_dir.exists()

    @patch('mdquery.mcp.MDQueryMCPServer._initialize_components')
    def test_mcp_server_initialization_error_handling(self, mock_init, tmp_path):
        """Test error handling during MCP server initialization."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Mock initialization to raise an exception
        mock_init.side_effect = Exception("Initialization failed")

        config = SimplifiedConfig(notes_dir=notes_dir)
        server = MDQueryMCPServer(config=config)

        # The server should be created but initialization will fail when called
        assert server.config == config
        assert server.db_manager is None  # Not initialized yet

    def test_obsidian_vault_configuration(self, tmp_path):
        """Test MCP server with Obsidian vault configuration."""
        # Create Obsidian vault structure
        vault_dir = tmp_path / "obsidian_vault"
        vault_dir.mkdir()
        (vault_dir / ".obsidian").mkdir()

        # Create some Obsidian-style files
        (vault_dir / "Daily Notes").mkdir()
        (vault_dir / "Daily Notes" / "2024-01-01.md").write_text("# Daily Note\n\n- Task 1\n- Task 2")
        (vault_dir / "Projects").mkdir()
        (vault_dir / "Projects" / "Project A.md").write_text("# Project A\n\n[[Daily Notes/2024-01-01]]")

        # Create configuration
        config = SimplifiedConfig(notes_dir=vault_dir)

        # Verify Obsidian detection
        assert config.config.note_system_type.value == "obsidian"

        # Initialize MCP server
        server = MDQueryMCPServer(config=config)

        # Verify server configuration
        assert server.notes_dirs == [vault_dir.resolve()]

    def test_configuration_persistence(self, tmp_path):
        """Test that configuration can be saved and reloaded."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create and save configuration
        original_config = SimplifiedConfig(notes_dir=notes_dir, auto_index=False)
        original_config.save_config()

        # Load configuration from saved file
        config_file = notes_dir / ".mdquery" / "config.json"
        loaded_config = SimplifiedConfig.load_config(config_file)

        # Create servers with both configurations
        original_server = MDQueryMCPServer(config=original_config)
        loaded_server = MDQueryMCPServer(config=loaded_config)

        # Verify they have the same configuration
        assert original_server.db_path == loaded_server.db_path
        assert original_server.cache_dir == loaded_server.cache_dir
        assert original_server.notes_dirs == loaded_server.notes_dirs
        assert original_server.auto_index == loaded_server.auto_index


if __name__ == "__main__":
    pytest.main([__file__])