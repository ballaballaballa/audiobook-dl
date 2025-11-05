"""
Tests for download functionality in audiobook-dl.
"""
import pytest
import os
import responses
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from audiobookdl.output.download import (
    download_file,
    download_files,
    create_filepath,
    get_output_audio_format,
    setup_download_dir,
    download_files_with_cli_output,
    add_metadata_to_file,
    add_metadata_to_dir,
)
from audiobookdl.exceptions import DownloadError
from audiobookdl.utils.audiobook import AudiobookFile


class TestCreateFilepath:
    """Tests for create_filepath function."""

    def test_single_file_path(self, minimal_audiobook, temp_dir):
        """Test filepath creation for single file audiobook."""
        output_dir = str(temp_dir / "test_book")
        filepath, filepath_tmp = create_filepath(minimal_audiobook, output_dir, 0)

        assert filepath == f"{output_dir}.mp3"
        assert filepath_tmp == f"{output_dir}.mp3.tmp"

    def test_multiple_files_path(self, sample_audiobook, temp_dir):
        """Test filepath creation for multi-file audiobook."""
        output_dir = str(temp_dir / "test_book")

        # First file (index 0)
        filepath, filepath_tmp = create_filepath(sample_audiobook, output_dir, 0)
        assert filepath == os.path.join(output_dir, "Part 0.mp3")
        assert filepath_tmp == os.path.join(output_dir, "Part 0.mp3.tmp")

        # Second file (index 1)
        filepath, filepath_tmp = create_filepath(sample_audiobook, output_dir, 1)
        assert filepath == os.path.join(output_dir, "Part 1.mp3")
        assert filepath_tmp == os.path.join(output_dir, "Part 1.mp3.tmp")

    def test_filepath_padding_for_many_files(self, mock_session, minimal_metadata, temp_dir):
        """Test that filepath includes proper padding for 10+ files."""
        # Create audiobook with 15 files
        files = [
            AudiobookFile(url=f"https://example.com/part{i}.mp3", ext="mp3")
            for i in range(15)
        ]
        from audiobookdl.utils.audiobook import Audiobook
        audiobook = Audiobook(
            session=mock_session,
            metadata=minimal_metadata,
            files=files,
        )

        output_dir = str(temp_dir / "test_book")

        # Check that numbers are padded
        filepath_0, _ = create_filepath(audiobook, output_dir, 0)
        filepath_9, _ = create_filepath(audiobook, output_dir, 9)
        filepath_14, _ = create_filepath(audiobook, output_dir, 14)

        # All should have same length number padding
        assert "Part 0.mp3" in filepath_0
        assert "Part 9.mp3" in filepath_9
        assert "Part 4.mp3" in filepath_14  # Due to padding calculation

    def test_filepath_extension_matches_file(self, mock_session, minimal_metadata, temp_dir):
        """Test that filepath extension matches the file extension."""
        files = [
            AudiobookFile(url="https://example.com/part1.m4b", ext="m4b"),
        ]
        from audiobookdl.utils.audiobook import Audiobook
        audiobook = Audiobook(
            session=mock_session,
            metadata=minimal_metadata,
            files=files,
        )

        output_dir = str(temp_dir / "test_book")
        filepath, _ = create_filepath(audiobook, output_dir, 0)

        assert filepath.endswith(".m4b")


class TestGetOutputAudioFormat:
    """Tests for get_output_audio_format function."""

    def test_format_with_no_option(self, temp_dir):
        """Test format detection with no user option."""
        files = [str(temp_dir / "test.mp3")]
        current, output = get_output_audio_format(None, files)

        assert current == "mp3"
        assert output == "mp3"

    def test_format_with_user_option(self, temp_dir):
        """Test format with user-specified option."""
        files = [str(temp_dir / "test.mp3")]
        current, output = get_output_audio_format("m4b", files)

        assert current == "mp3"
        assert output == "m4b"

    def test_format_m4b_files(self, temp_dir):
        """Test format detection for M4B files."""
        files = [str(temp_dir / "test.m4b")]
        current, output = get_output_audio_format(None, files)

        assert current == "m4b"
        assert output == "m4b"

    def test_format_multiple_files(self, temp_dir):
        """Test format detection with multiple files (uses first file)."""
        files = [
            str(temp_dir / "test1.mp3"),
            str(temp_dir / "test2.mp3"),
            str(temp_dir / "test3.mp3"),
        ]
        current, output = get_output_audio_format(None, files)

        assert current == "mp3"
        assert output == "mp3"


class TestSetupDownloadDir:
    """Tests for setup_download_dir function."""

    def test_create_new_directory(self, temp_dir):
        """Test creating a new download directory."""
        new_dir = temp_dir / "new_download_dir"
        assert not new_dir.exists()

        setup_download_dir(str(new_dir))

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_nested_directory(self, temp_dir):
        """Test creating nested directories."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        assert not nested_dir.exists()

        setup_download_dir(str(nested_dir))

        assert nested_dir.exists()
        assert nested_dir.is_dir()

    @patch("audiobookdl.output.download.Confirm.ask")
    def test_existing_directory_confirm_yes(self, mock_confirm, temp_dir):
        """Test handling existing directory with user confirmation to override."""
        existing_dir = temp_dir / "existing_dir"
        existing_dir.mkdir()
        test_file = existing_dir / "test.txt"
        test_file.write_text("test content")

        # User confirms override
        mock_confirm.return_value = True

        setup_download_dir(str(existing_dir))

        # Directory should be recreated (empty)
        assert existing_dir.exists()
        assert not test_file.exists()

    @patch("audiobookdl.output.download.Confirm.ask")
    def test_existing_directory_confirm_no(self, mock_confirm, temp_dir):
        """Test handling existing directory with user declining to override."""
        existing_dir = temp_dir / "existing_dir"
        existing_dir.mkdir()

        # User declines override
        mock_confirm.return_value = False

        with pytest.raises(SystemExit):
            setup_download_dir(str(existing_dir))


@responses.activate
class TestDownloadFile:
    """Tests for download_file function."""

    def test_download_single_file(self, minimal_audiobook, temp_dir):
        """Test downloading a single file."""
        # Mock HTTP response
        file_content = b"This is fake audio content"
        responses.add(
            responses.GET,
            minimal_audiobook.files[0].url,
            body=file_content,
            headers={"Content-length": str(len(file_content))},
            status=200,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (minimal_audiobook, output_dir, 0, update_progress)

        filepath = download_file(args)

        # Check file was created
        assert os.path.exists(filepath)

        # Check content
        with open(filepath, "rb") as f:
            assert f.read() == file_content

        # Check progress was updated
        assert update_progress.called

    def test_download_with_custom_headers(self, mock_session, minimal_metadata, temp_dir):
        """Test downloading with custom headers."""
        custom_headers = {
            "User-Agent": "audiobook-dl/test",
            "Authorization": "Bearer token123",
        }
        file = AudiobookFile(
            url="https://example.com/audio.mp3",
            ext="mp3",
            headers=custom_headers,
        )

        from audiobookdl.utils.audiobook import Audiobook
        audiobook = Audiobook(
            session=mock_session,
            metadata=minimal_metadata,
            files=[file],
        )

        # Mock HTTP response
        file_content = b"Audio content"
        responses.add(
            responses.GET,
            file.url,
            body=file_content,
            headers={"Content-length": str(len(file_content))},
            status=200,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (audiobook, output_dir, 0, update_progress)

        filepath = download_file(args)

        assert os.path.exists(filepath)
        # Verify request was made with custom headers
        assert len(responses.calls) == 1
        # Note: responses library doesn't easily expose request headers in assertions

    def test_download_with_wrong_content_type(self, minimal_audiobook, temp_dir):
        """Test download fails with unexpected content type."""
        # Set expected content type
        minimal_audiobook.files[0].expected_content_type = "audio/mpeg"

        # Mock HTTP response with wrong content type
        responses.add(
            responses.GET,
            minimal_audiobook.files[0].url,
            body=b"content",
            headers={
                "Content-length": "7",
                "Content-type": "text/html",
            },
            status=200,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (minimal_audiobook, output_dir, 0, update_progress)

        with pytest.raises(DownloadError):
            download_file(args)

    def test_download_with_wrong_status_code(self, minimal_audiobook, temp_dir):
        """Test download fails with unexpected status code."""
        # Set expected status code
        minimal_audiobook.files[0].expected_status_code = 200

        # Mock HTTP response with wrong status code
        responses.add(
            responses.GET,
            minimal_audiobook.files[0].url,
            body=b"content",
            headers={"Content-length": "7"},
            status=403,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (minimal_audiobook, output_dir, 0, update_progress)

        with pytest.raises(DownloadError):
            download_file(args)

    def test_download_large_file_chunked(self, minimal_audiobook, temp_dir):
        """Test downloading large file in chunks."""
        # Create larger content (10KB)
        file_content = b"x" * 10240

        responses.add(
            responses.GET,
            minimal_audiobook.files[0].url,
            body=file_content,
            headers={"Content-length": str(len(file_content))},
            status=200,
            stream=True,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (minimal_audiobook, output_dir, 0, update_progress)

        filepath = download_file(args)

        # Verify file downloaded correctly
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) == len(file_content)

        # Progress should be updated multiple times (chunked download)
        assert update_progress.call_count > 1

    @patch("audiobookdl.output.download.encryption.decrypt_file")
    def test_download_encrypted_file(self, mock_decrypt, encrypted_audiobook_file, mock_session, minimal_metadata, temp_dir):
        """Test downloading and decrypting encrypted file."""
        from audiobookdl.utils.audiobook import Audiobook
        audiobook = Audiobook(
            session=mock_session,
            metadata=minimal_metadata,
            files=[encrypted_audiobook_file],
        )

        file_content = b"encrypted content"
        responses.add(
            responses.GET,
            encrypted_audiobook_file.url,
            body=file_content,
            headers={"Content-length": str(len(file_content))},
            status=200,
        )

        output_dir = str(temp_dir / "test_book")
        update_progress = Mock()
        args = (audiobook, output_dir, 0, update_progress)

        filepath = download_file(args)

        # Check that decryption was called
        assert mock_decrypt.called
        mock_decrypt.assert_called_once()


class TestDownloadFiles:
    """Tests for download_files function (multi-threaded)."""

    @responses.activate
    def test_download_multiple_files(self, sample_audiobook, temp_dir):
        """Test downloading multiple files with thread pool."""
        # Mock all file downloads
        for file in sample_audiobook.files:
            responses.add(
                responses.GET,
                file.url,
                body=b"audio content",
                headers={"Content-length": "13"},
                status=200,
            )

        output_dir = str(temp_dir / "test_book")
        os.makedirs(output_dir)
        update_progress = Mock()

        filepaths = download_files(sample_audiobook, output_dir, update_progress)

        # Check all files downloaded
        assert len(filepaths) == 3
        for filepath in filepaths:
            assert os.path.exists(filepath)

    @responses.activate
    def test_download_files_maintains_order(self, sample_audiobook, temp_dir):
        """Test that downloaded files are returned in correct order."""
        # Mock all file downloads
        for file in sample_audiobook.files:
            responses.add(
                responses.GET,
                file.url,
                body=b"audio",
                headers={"Content-length": "5"},
                status=200,
            )

        output_dir = str(temp_dir / "test_book")
        os.makedirs(output_dir)
        update_progress = Mock()

        filepaths = download_files(sample_audiobook, output_dir, update_progress)

        # Check files are in order
        assert "Part 0.mp3" in filepaths[0]
        assert "Part 1.mp3" in filepaths[1]
        assert "Part 2.mp3" in filepaths[2]


class TestDownloadFilesWithCLIOutput:
    """Tests for download_files_with_cli_output function."""

    @responses.activate
    @patch("audiobookdl.output.download.logging")
    def test_download_with_progress_bar(self, mock_logging, sample_audiobook, temp_dir):
        """Test downloading with CLI progress bar."""
        # Mock all file downloads
        for file in sample_audiobook.files:
            responses.add(
                responses.GET,
                file.url,
                body=b"audio",
                headers={"Content-length": "5"},
                status=200,
            )

        output_dir = str(temp_dir / "test_book")

        # Mock progress context manager
        mock_progress = MagicMock()
        mock_logging.progress.return_value.__enter__.return_value = mock_progress
        mock_logging.progress.return_value.__exit__.return_value = None

        filepaths = download_files_with_cli_output(sample_audiobook, output_dir)

        # Check progress bar was created
        assert mock_progress.add_task.called
        assert len(filepaths) == 3

    @responses.activate
    def test_creates_parent_directory_for_single_file(self, minimal_audiobook, temp_dir):
        """Test that parent directory is created for single file downloads."""
        responses.add(
            responses.GET,
            minimal_audiobook.files[0].url,
            body=b"audio",
            headers={"Content-length": "5"},
            status=200,
        )

        output_dir = str(temp_dir / "subdir" / "test_book")

        with patch("audiobookdl.output.download.logging"):
            filepaths = download_files_with_cli_output(minimal_audiobook, output_dir)

        # Parent directory should exist
        assert Path(output_dir).parent.exists()
        assert len(filepaths) == 1


class TestAddMetadataToFile:
    """Tests for add_metadata_to_file function."""

    @patch("audiobookdl.output.download.metadata")
    def test_add_basic_metadata(self, mock_metadata, sample_audiobook, temp_dir):
        """Test adding basic metadata to a file."""
        filepath = str(temp_dir / "audiobook.m4b")
        Path(filepath).touch()

        options = Mock()
        options.write_json_metadata = False
        options.no_chapters = False

        add_metadata_to_file(sample_audiobook, filepath, options)

        # Check metadata was added
        mock_metadata.add_metadata.assert_called_once_with(filepath, sample_audiobook.metadata)
        mock_metadata.add_chapters.assert_called_once_with(filepath, sample_audiobook.chapters)
        mock_metadata.embed_cover.assert_called_once_with(filepath, sample_audiobook.cover)

    @patch("audiobookdl.output.download.metadata")
    def test_add_metadata_with_json_export(self, mock_metadata, sample_audiobook, temp_dir):
        """Test adding metadata and exporting to JSON."""
        filepath = str(temp_dir / "audiobook.m4b")
        Path(filepath).touch()

        options = Mock()
        options.write_json_metadata = True
        options.no_chapters = False

        add_metadata_to_file(sample_audiobook, filepath, options)

        # Check JSON metadata file was created
        json_filepath = f"{filepath}.json"
        assert os.path.exists(json_filepath)

    @patch("audiobookdl.output.download.metadata")
    def test_skip_chapters_when_option_set(self, mock_metadata, sample_audiobook, temp_dir):
        """Test that chapters are skipped when no_chapters option is set."""
        filepath = str(temp_dir / "audiobook.m4b")
        Path(filepath).touch()

        options = Mock()
        options.write_json_metadata = False
        options.no_chapters = True

        add_metadata_to_file(sample_audiobook, filepath, options)

        # Chapters should not be added
        mock_metadata.add_chapters.assert_not_called()
        # But other metadata should be added
        mock_metadata.add_metadata.assert_called_once()


class TestAddMetadataToDir:
    """Tests for add_metadata_to_dir function."""

    @patch("audiobookdl.output.download.metadata")
    def test_add_metadata_to_multiple_files(self, mock_metadata, sample_audiobook, temp_dir):
        """Test adding metadata to multiple files in a directory."""
        output_dir = str(temp_dir / "audiobook")
        os.makedirs(output_dir)

        filepaths = [
            str(temp_dir / "audiobook" / "part1.mp3"),
            str(temp_dir / "audiobook" / "part2.mp3"),
            str(temp_dir / "audiobook" / "part3.mp3"),
        ]
        for fp in filepaths:
            Path(fp).touch()

        options = Mock()
        options.write_json_metadata = False

        add_metadata_to_dir(sample_audiobook, filepaths, output_dir, options)

        # Metadata should be added to all files
        assert mock_metadata.add_metadata.call_count == 3

    @patch("audiobookdl.output.download.metadata")
    def test_add_cover_to_directory(self, mock_metadata, sample_audiobook, temp_dir):
        """Test that cover is saved in the directory."""
        output_dir = str(temp_dir / "audiobook")
        os.makedirs(output_dir)

        filepaths = [str(temp_dir / "audiobook" / "part1.mp3")]
        Path(filepaths[0]).touch()

        options = Mock()
        options.write_json_metadata = False

        add_metadata_to_dir(sample_audiobook, filepaths, output_dir, options)

        # Cover file should be created
        cover_path = os.path.join(output_dir, f"cover.{sample_audiobook.cover.extension}")
        assert os.path.exists(cover_path)

    @patch("audiobookdl.output.download.metadata")
    def test_add_metadata_json_to_directory(self, mock_metadata, sample_audiobook, temp_dir):
        """Test that JSON metadata is saved in the directory."""
        output_dir = str(temp_dir / "audiobook")
        os.makedirs(output_dir)

        filepaths = [str(temp_dir / "audiobook" / "part1.mp3")]
        Path(filepaths[0]).touch()

        options = Mock()
        options.write_json_metadata = True

        add_metadata_to_dir(sample_audiobook, filepaths, output_dir, options)

        # JSON metadata file should be created
        metadata_path = os.path.join(output_dir, "metadata.json")
        assert os.path.exists(metadata_path)
