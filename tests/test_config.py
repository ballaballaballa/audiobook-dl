"""
Tests for configuration management in audiobook-dl.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch

from audiobookdl.config import (
    Config,
    SourceConfig,
    load_config,
    config_dir,
    get_config_location,
    read_config,
    structure_config,
)
from audiobookdl.exceptions import ConfigNotFound


class TestSourceConfig:
    """Tests for SourceConfig class."""

    def test_source_config_creation(self):
        """Test creating a SourceConfig."""
        config = SourceConfig(
            username="user@example.com",
            password="password123",
            library="main",
            cookie_file="/path/to/cookies.txt"
        )

        assert config.username == "user@example.com"
        assert config.password == "password123"
        assert config.library == "main"
        assert config.cookie_file == "/path/to/cookies.txt"

    def test_source_config_optional_fields(self):
        """Test SourceConfig with optional fields as None."""
        config = SourceConfig(
            username=None,
            password=None,
            library=None,
            cookie_file=None
        )

        assert config.username is None
        assert config.password is None
        assert config.library is None
        assert config.cookie_file is None

    def test_source_config_partial_fields(self):
        """Test SourceConfig with only some fields set."""
        config = SourceConfig(
            username="user@example.com",
            password="pass",
            library=None,
            cookie_file=None
        )

        assert config.username == "user@example.com"
        assert config.password == "pass"
        assert config.library is None


class TestConfig:
    """Tests for Config class."""

    def test_config_creation(self):
        """Test creating a Config object."""
        source_config = SourceConfig(
            username="user", password="pass", library=None, cookie_file=None
        )

        config = Config(
            sources={"storytel": source_config},
            output_template="{author}/{title}",
            database_directory="/tmp/db",
            skip_downloaded=True,
            combine=True,
            remove_chars=":*?",
            no_chapters=False,
            output_format="m4b",
            write_json_metadata=True,
            mp4_audio_encoder="aac"
        )

        assert "storytel" in config.sources
        assert config.output_template == "{author}/{title}"
        assert config.skip_downloaded is True
        assert config.output_format == "m4b"

    def test_config_with_multiple_sources(self):
        """Test Config with multiple source configurations."""
        sources = {
            "storytel": SourceConfig("user1", "pass1", None, None),
            "nextory": SourceConfig("user2", "pass2", None, None),
            "librivox": SourceConfig(None, None, None, None),
        }

        config = Config(
            sources=sources,
            output_template=None,
            database_directory=None,
            skip_downloaded=None,
            combine=None,
            remove_chars=None,
            no_chapters=None,
            output_format=None,
            write_json_metadata=None,
            mp4_audio_encoder=None
        )

        assert len(config.sources) == 3
        assert "storytel" in config.sources
        assert "nextory" in config.sources
        assert "librivox" in config.sources


class TestConfigDir:
    """Tests for config_dir function."""

    @patch("audiobookdl.config.platformdirs.user_config_dir")
    def test_config_dir_uses_platformdirs(self, mock_user_config_dir):
        """Test that config_dir uses platformdirs."""
        mock_user_config_dir.return_value = "/home/user/.config/audiobook-dl"

        result = config_dir()

        mock_user_config_dir.assert_called_once_with("audiobook-dl", "jo1gi")
        assert result == "/home/user/.config/audiobook-dl"

    @patch("audiobookdl.config.platformdirs.user_config_dir")
    def test_config_dir_linux(self, mock_user_config_dir):
        """Test config directory on Linux."""
        mock_user_config_dir.return_value = "/home/user/.config/audiobook-dl"

        result = config_dir()

        assert "/audiobook-dl" in result

    @patch("audiobookdl.config.platformdirs.user_config_dir")
    def test_config_dir_returns_string(self, mock_user_config_dir):
        """Test that config_dir returns a string path."""
        mock_user_config_dir.return_value = "/path/to/config"

        result = config_dir()

        assert isinstance(result, str)


class TestGetConfigLocation:
    """Tests for get_config_location function."""

    def test_get_config_location_default(self):
        """Test getting default config location."""
        with patch("audiobookdl.config.config_dir") as mock_config_dir:
            mock_config_dir.return_value = "/home/user/.config/audiobook-dl"

            result = get_config_location(None)

            assert result == "/home/user/.config/audiobook-dl/audiobook-dl.toml"

    def test_get_config_location_with_overwrite(self, temp_dir):
        """Test getting config location with overwrite path."""
        custom_config = temp_dir / "custom-config.toml"
        custom_config.touch()

        result = get_config_location(str(custom_config))

        assert result == str(custom_config)

    def test_get_config_location_overwrite_not_exists(self):
        """Test that overwrite path must exist."""
        with pytest.raises(ConfigNotFound):
            get_config_location("/nonexistent/config.toml")

    def test_get_config_location_empty_overwrite(self):
        """Test with empty string overwrite (treated as None)."""
        with patch("audiobookdl.config.config_dir") as mock_config_dir:
            mock_config_dir.return_value = "/home/user/.config/audiobook-dl"

            # Empty string is falsy, should use default
            result = get_config_location("")

            assert result == "/home/user/.config/audiobook-dl/audiobook-dl.toml"


class TestReadConfig:
    """Tests for read_config function."""

    def test_read_existing_config(self, temp_dir):
        """Test reading an existing config file."""
        config_file = temp_dir / "config.toml"
        config_content = """
[sources.storytel]
username = "user@example.com"
password = "secret"

output_template = "{author}/{title}"
"""
        config_file.write_text(config_content)

        result = read_config(str(config_file))

        assert "sources" in result
        assert "storytel" in result["sources"]
        assert result["sources"]["storytel"]["username"] == "user@example.com"
        assert result["output_template"] == "{author}/{title}"

    def test_read_nonexistent_config(self):
        """Test reading non-existent config returns empty dict."""
        result = read_config("/nonexistent/config.toml")

        assert result == {}

    def test_read_empty_config(self, temp_dir):
        """Test reading empty config file."""
        config_file = temp_dir / "empty.toml"
        config_file.write_text("")

        result = read_config(str(config_file))

        assert result == {}

    def test_read_config_with_comments(self, temp_dir):
        """Test reading config with comments."""
        config_file = temp_dir / "config.toml"
        config_content = """
# This is a comment
output_format = "m4b"  # Another comment
# More comments
combine = true
"""
        config_file.write_text(config_content)

        result = read_config(str(config_file))

        assert result["output_format"] == "m4b"
        assert result["combine"] is True

    def test_read_config_with_multiple_sources(self, temp_dir):
        """Test reading config with multiple sources."""
        config_file = temp_dir / "config.toml"
        config_content = """
[sources.storytel]
username = "storytel_user"

[sources.nextory]
username = "nextory_user"
cookie_file = "cookies.txt"
"""
        config_file.write_text(config_content)

        result = read_config(str(config_file))

        assert len(result["sources"]) == 2
        assert "storytel" in result["sources"]
        assert "nextory" in result["sources"]


class TestStructureConfig:
    """Tests for structure_config function."""

    def test_structure_empty_config(self):
        """Test structuring empty config dict."""
        result = structure_config("/config.toml", {})

        assert isinstance(result, Config)
        assert len(result.sources) == 0
        assert result.output_template is None

    def test_structure_config_with_sources(self):
        """Test structuring config with sources."""
        config_dict = {
            "sources": {
                "storytel": {
                    "username": "user@example.com",
                    "password": "secret"
                }
            }
        }

        result = structure_config("/config.toml", config_dict)

        assert "storytel" in result.sources
        assert result.sources["storytel"].username == "user@example.com"
        assert result.sources["storytel"].password == "secret"

    def test_structure_config_with_all_options(self):
        """Test structuring config with all options."""
        config_dict = {
            "output_template": "{author}/{title}",
            "database_directory": "/tmp/db",
            "skip_downloaded": True,
            "combine": True,
            "remove_chars": ":*?",
            "no_chapters": False,
            "output_format": "m4b",
            "write_json_metadata": True,
            "mp4_audio_encoder": "aac"
        }

        result = structure_config("/config.toml", config_dict)

        assert result.output_template == "{author}/{title}"
        assert result.database_directory == "/tmp/db"
        assert result.skip_downloaded is True
        assert result.combine is True
        assert result.remove_chars == ":*?"
        assert result.no_chapters is False
        assert result.output_format == "m4b"
        assert result.write_json_metadata is True
        assert result.mp4_audio_encoder == "aac"

    def test_structure_config_cookie_file_relative_path(self, temp_dir):
        """Test that cookie_file path is made relative to config location."""
        config_location = str(temp_dir / "config.toml")
        config_dict = {
            "sources": {
                "nextory": {
                    "cookie_file": str(temp_dir / "cookies.txt")
                }
            }
        }

        result = structure_config(config_location, config_dict)

        # Cookie file should be relative path
        assert result.sources["nextory"].cookie_file is not None

    def test_structure_config_source_without_cookie_file(self):
        """Test source config without cookie_file."""
        config_dict = {
            "sources": {
                "storytel": {
                    "username": "user",
                    "password": "pass"
                }
            }
        }

        result = structure_config("/config.toml", config_dict)

        assert result.sources["storytel"].cookie_file is None


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_from_file(self, temp_dir):
        """Test loading complete config from file."""
        config_file = temp_dir / "config.toml"
        config_content = """
[sources.storytel]
username = "user@example.com"
password = "secret"

output_template = "{author}/{title}"
output_format = "m4b"
combine = true
"""
        config_file.write_text(config_content)

        result = load_config(str(config_file))

        assert isinstance(result, Config)
        assert "storytel" in result.sources
        assert result.output_template == "{author}/{title}"
        assert result.output_format == "m4b"
        assert result.combine is True

    def test_load_config_with_overwrite(self, temp_dir):
        """Test loading config from custom location."""
        custom_config = temp_dir / "custom.toml"
        custom_config.write_text('output_format = "mp3"')

        result = load_config(str(custom_config))

        assert result.output_format == "mp3"

    def test_load_config_missing_overwrite_raises(self):
        """Test that missing overwrite location raises ConfigNotFound."""
        with pytest.raises(ConfigNotFound):
            load_config("/nonexistent/config.toml")


class TestConfigIntegration:
    """Integration tests for config loading."""

    def test_full_config_workflow(self, temp_dir):
        """Test complete config loading workflow."""
        config_file = temp_dir / "audiobook-dl.toml"
        config_content = """
# Audiobook-dl configuration

[sources.storytel]
username = "storytel@example.com"
password = "storytel_pass"

[sources.nextory]
cookie_file = "nextory_cookies.txt"

output_template = "{author}/{series}/{title}"
output_format = "m4b"
database_directory = "/tmp/audiobook-dl"
skip_downloaded = true
combine = true
remove_chars = ":*?<>|"
no_chapters = false
write_json_metadata = true
mp4_audio_encoder = "aac"
"""
        config_file.write_text(config_content)

        # Load config
        config = load_config(str(config_file))

        # Verify sources
        assert len(config.sources) == 2
        assert config.sources["storytel"].username == "storytel@example.com"
        assert config.sources["nextory"].cookie_file is not None

        # Verify options
        assert config.output_template == "{author}/{series}/{title}"
        assert config.output_format == "m4b"
        assert config.skip_downloaded is True
        assert config.combine is True
        assert config.remove_chars == ":*?<>|"
        assert config.write_json_metadata is True

    def test_minimal_config(self, temp_dir):
        """Test minimal valid config."""
        config_file = temp_dir / "minimal.toml"
        config_file.write_text("")

        config = load_config(str(config_file))

        assert isinstance(config, Config)
        assert len(config.sources) == 0

    def test_config_with_only_sources(self, temp_dir):
        """Test config with only source definitions."""
        config_file = temp_dir / "sources-only.toml"
        config_content = """
[sources.librivox]
username = "librivox_user"

[sources.storytel]
username = "storytel_user"
password = "storytel_pass"
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert len(config.sources) == 2
        assert config.output_template is None
        assert config.output_format is None


class TestConfigEdgeCases:
    """Tests for edge cases in config handling."""

    def test_config_with_unicode(self, temp_dir):
        """Test config with Unicode characters."""
        config_file = temp_dir / "unicode.toml"
        config_content = """
output_template = "書籍/{author}/{title}"
remove_chars = "™®©"
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert "書籍" in config.output_template
        assert config.remove_chars == "™®©"

    def test_config_with_special_chars_in_password(self, temp_dir):
        """Test config with special characters in password."""
        config_file = temp_dir / "special-pass.toml"
        config_content = """
[sources.storytel]
username = "user"
password = "p@$$w0rd!#%"
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.sources["storytel"].password == "p@$$w0rd!#%"

    def test_config_with_boolean_values(self, temp_dir):
        """Test config with various boolean values."""
        config_file = temp_dir / "booleans.toml"
        config_content = """
skip_downloaded = true
combine = false
no_chapters = true
write_json_metadata = false
"""
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.skip_downloaded is True
        assert config.combine is False
        assert config.no_chapters is True
        assert config.write_json_metadata is False

    def test_config_with_very_long_template(self, temp_dir):
        """Test config with very long output template."""
        config_file = temp_dir / "long-template.toml"
        long_template = "{author}" + "/{series}" * 10 + "/{title}"
        config_content = f'output_template = "{long_template}"'
        config_file.write_text(config_content)

        config = load_config(str(config_file))

        assert config.output_template == long_template
        assert config.output_template.count("/series") == 10
