"""
Tests for the simplified configuration system.

This module tests the SimplifiedConfig class and its integration with
the MCP server, ensuring proper path-first configuration, directory
creation, and error handling.
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from mdquery.config import (
    SimplifiedConfig,
    MCPServerConfig,
    NoteSystemType,
    create_helpful_error_message
)
from mdquery.exceptions import (
    ConfigurationError,
    DirectoryNotFoundError,
    FileAccessError
)


class TestSimplifiedConfig:
    """Test cases for SimplifiedConfig class."""

    def test_basic_configuration_creation(self, tmp_path):
        """Test basic configuration creation with valid notes directory."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)

        assert config.config.notes_dir == notes_dir.resolve()
        assert config.config.db_path == notes_dir / ".mdquery" / "mdquery.db"
        assert config.config.cache_dir == notes_dir / ".mdquery" / "cache"
        assert config.config.auto_index is True
        assert config.config.note_system_type == NoteSystemType.GENERIC

    def test_automatic_directory_creation(self, tmp_path):
        """Test that .mdquery directories are created automatically."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)

        # Check that directories were created
        assert (notes_dir / ".mdquery").exists()
        assert (notes_dir / ".mdquery" / "cache").exists()
        assert config.config.db_path.parent.exists()

    def test_custom_db_and_cache_paths(self, tmp_path):
        """Test configuration with custom database and cache paths."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        custom_db = tmp_path / "custom" / "db.sqlite"
        custom_cache = tmp_path / "custom" / "cache"

        config = SimplifiedConfig(
            notes_dir=notes_dir,
            db_path=custom_db,
            cache_dir=custom_cache
        )

        assert config.config.db_path == custom_db.resolve()
        assert config.config.cache_dir == custom_cache.resolve()

        # Check that custom directories were created
        assert custom_db.parent.exists()
        assert custom_cache.exists()

    def test_obsidian_vault_detection(self, tmp_path):
        """Test detection of Obsidian vault."""
        notes_dir = tmp_path / "obsidian_vault"
        notes_dir.mkdir()
        (notes_dir / ".obsidian").mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)

        assert config.config.note_system_type == NoteSystemType.OBSIDIAN

    def test_joplin_detection(self, tmp_path):
        """Test detection of Joplin notebooks."""
        notes_dir = tmp_path / "joplin_notes"
        notes_dir.mkdir()
        (notes_dir / "test.jex").touch()

        config = SimplifiedConfig(notes_dir=notes_dir)

        assert config.config.note_system_type == NoteSystemType.JOPLIN

    def test_logseq_detection(self, tmp_path):
        """Test detection of Logseq graph."""
        notes_dir = tmp_path / "logseq_graph"
        notes_dir.mkdir()
        (notes_dir / "logseq").mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)

        assert config.config.note_system_type == NoteSystemType.LOGSEQ

    def test_foam_detection(self, tmp_path):
        """Test detection of Foam workspace."""
        notes_dir = tmp_path / "foam_workspace"
        notes_dir.mkdir()
        (notes_dir / ".foam").mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)

        assert config.config.note_system_type == NoteSystemType.FOAM

    def test_nonexistent_notes_directory_error(self, tmp_path):
        """Test error handling for nonexistent notes directory."""
        nonexistent_dir = tmp_path / "does_not_exist"

        with pytest.raises(DirectoryNotFoundError) as exc_info:
            SimplifiedConfig(notes_dir=nonexistent_dir)

        assert "does not exist" in str(exc_info.value)
        assert exc_info.value.file_path == nonexistent_dir.resolve()

    def test_notes_path_is_file_error(self, tmp_path):
        """Test error handling when notes path is a file, not directory."""
        notes_file = tmp_path / "notes.txt"
        notes_file.touch()

        with pytest.raises(ConfigurationError) as exc_info:
            SimplifiedConfig(notes_dir=notes_file)

        assert "not a directory" in str(exc_info.value)

    def test_empty_notes_directory_error(self):
        """Test error handling for empty notes directory path."""
        with pytest.raises(ConfigurationError) as exc_info:
            SimplifiedConfig(notes_dir="")

        assert "required" in str(exc_info.value)

    def test_none_notes_directory_error(self):
        """Test error handling for None notes directory path."""
        with pytest.raises(ConfigurationError) as exc_info:
            SimplifiedConfig(notes_dir=None)

        assert "required" in str(exc_info.value)

    def test_path_expansion(self, tmp_path):
        """Test that paths are properly expanded (~ and relative paths)."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Test with relative path by changing to the temp directory
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            config = SimplifiedConfig(notes_dir="notes")
            assert config.config.notes_dir.is_absolute()
            assert config.config.notes_dir == notes_dir.resolve()
        finally:
            os.chdir(original_cwd)

    def test_configuration_serialization(self, tmp_path):
        """Test configuration serialization to dictionary."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)
        config_dict = config.get_mcp_config()

        assert "notes_dir" in config_dict
        assert "db_path" in config_dict
        assert "cache_dir" in config_dict
        assert "auto_index" in config_dict
        assert "note_system_type" in config_dict

        assert config_dict["notes_dir"] == str(notes_dir.resolve())
        assert config_dict["auto_index"] is True

    def test_save_and_load_config(self, tmp_path):
        """Test saving and loading configuration from JSON file."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Create and save configuration
        original_config = SimplifiedConfig(notes_dir=notes_dir, auto_index=False)
        config_file = tmp_path / "config.json"
        original_config.save_config(config_file)

        # Load configuration
        loaded_config = SimplifiedConfig.load_config(config_file)

        assert loaded_config.config.notes_dir == original_config.config.notes_dir
        assert loaded_config.config.db_path == original_config.config.db_path
        assert loaded_config.config.cache_dir == original_config.config.cache_dir
        assert loaded_config.config.auto_index == original_config.config.auto_index

    def test_save_config_default_location(self, tmp_path):
        """Test saving configuration to default location."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)
        config.save_config()

        # Check that config was saved to default location
        default_config_path = notes_dir / ".mdquery" / "config.json"
        assert default_config_path.exists()

        # Verify content
        with open(default_config_path, 'r') as f:
            saved_data = json.load(f)

        assert "version" in saved_data
        assert "config" in saved_data
        assert saved_data["config"]["notes_dir"] == str(notes_dir.resolve())

    def test_load_invalid_config_file(self, tmp_path):
        """Test error handling for invalid configuration file."""
        invalid_config = tmp_path / "invalid.json"
        invalid_config.write_text("invalid json content")

        with pytest.raises(ConfigurationError) as exc_info:
            SimplifiedConfig.load_config(invalid_config)

        assert "Invalid JSON" in str(exc_info.value)

    def test_load_nonexistent_config_file(self, tmp_path):
        """Test error handling for nonexistent configuration file."""
        nonexistent_config = tmp_path / "does_not_exist.json"

        with pytest.raises(FileAccessError) as exc_info:
            SimplifiedConfig.load_config(nonexistent_config)

        assert "does not exist" in str(exc_info.value)

    @patch('mdquery.config.SimplifiedConfig._check_directory_access')
    def test_permission_error_handling(self, mock_check_access, tmp_path):
        """Test error handling for permission issues."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        # Mock permission check to return False
        mock_check_access.return_value = False

        with pytest.raises(FileAccessError) as exc_info:
            SimplifiedConfig(notes_dir=notes_dir)

        assert "Cannot read from" in str(exc_info.value)

    def test_string_representation(self, tmp_path):
        """Test string representation of configuration."""
        notes_dir = tmp_path / "notes"
        notes_dir.mkdir()

        config = SimplifiedConfig(notes_dir=notes_dir)
        config_str = str(config)

        assert "SimplifiedConfig" in config_str
        assert str(notes_dir.resolve()) in config_str
        assert "generic" in config_str  # note system type


class TestHelpfulErrorMessages:
    """Test cases for helpful error message generation."""

    def test_directory_not_found_error_message(self, tmp_path):
        """Test helpful error message for directory not found."""
        nonexistent_dir = tmp_path / "does_not_exist"
        error = DirectoryNotFoundError(
            f"Directory not found: {nonexistent_dir}",
            file_path=nonexistent_dir
        )

        message = create_helpful_error_message(error, str(nonexistent_dir))

        assert "❌ Notes directory not found" in message
        assert "💡 Solutions:" in message
        assert "Check that the path exists" in message
        assert "📝 Example valid paths:" in message

    def test_file_access_error_message(self, tmp_path):
        """Test helpful error message for file access issues."""
        notes_dir = tmp_path / "notes"
        error = FileAccessError(
            f"Cannot access directory: {notes_dir}",
            file_path=notes_dir
        )

        message = create_helpful_error_message(error, str(notes_dir))

        assert "❌ Cannot access directory" in message
        assert "💡 Solutions:" in message
        assert "Check directory permissions" in message
        assert "🔧 Quick fixes:" in message

    def test_configuration_error_message(self):
        """Test helpful error message for configuration issues."""
        error = ConfigurationError(
            "Invalid configuration",
            context={"suggestion": "Check your settings"}
        )

        message = create_helpful_error_message(error)

        assert "❌ Configuration error" in message
        assert "💡 Suggestion: Check your settings" in message

    def test_generic_error_message(self):
        """Test helpful error message for generic errors."""
        error = ValueError("Something went wrong")

        message = create_helpful_error_message(error)

        assert "❌ Unexpected error" in message
        assert "💡 This might be a bug" in message
        assert "🐛 If the problem persists" in message


class TestMCPServerConfig:
    """Test cases for MCPServerConfig data class."""

    def test_config_to_dict(self, tmp_path):
        """Test conversion of config to dictionary."""
        notes_dir = tmp_path / "notes"
        db_path = tmp_path / "db.sqlite"
        cache_dir = tmp_path / "cache"

        config = MCPServerConfig(
            notes_dir=notes_dir,
            db_path=db_path,
            cache_dir=cache_dir,
            auto_index=False,
            note_system_type=NoteSystemType.OBSIDIAN
        )

        config_dict = config.to_dict()

        assert config_dict["notes_dir"] == str(notes_dir)
        assert config_dict["db_path"] == str(db_path)
        assert config_dict["cache_dir"] == str(cache_dir)
        assert config_dict["auto_index"] is False
        assert config_dict["note_system_type"] == "obsidian"


if __name__ == "__main__":
    pytest.main([__file__])