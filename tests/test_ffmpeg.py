"""
Tests for FFmpeg operations in audiobook-dl.
"""
import pytest
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

from audiobookdl.output.output import (
    combine_audiofiles,
    convert_output,
    get_extension,
    can_copy_codec,
    check_encoder_available,
    get_audio_bitrate,
    gen_output_location,
    _fix_output,
    _remove_chars,
    get_max_name_length,
)
from audiobookdl.exceptions import FailedCombining, MissingEncoder


class TestGetExtension:
    """Tests for get_extension function."""

    def test_get_mp3_extension(self):
        """Test extracting .mp3 extension."""
        assert get_extension("/path/to/file.mp3") == "mp3"

    def test_get_m4b_extension(self):
        """Test extracting .m4b extension."""
        assert get_extension("/path/to/audiobook.m4b") == "m4b"

    def test_get_extension_no_path(self):
        """Test extension from filename only."""
        assert get_extension("audiobook.mp4") == "mp4"

    def test_get_extension_multiple_dots(self):
        """Test extension with multiple dots in filename."""
        assert get_extension("my.file.with.dots.mp3") == "mp3"

    def test_get_extension_uppercase(self):
        """Test uppercase extension."""
        assert get_extension("FILE.MP3") == "MP3"


class TestCanCopyCodec:
    """Tests for can_copy_codec function."""

    def test_mkv_can_copy(self):
        """Test that MKV can copy codec from any source."""
        assert can_copy_codec("mp3", "mkv") is True
        assert can_copy_codec("m4a", "mkv") is True
        assert can_copy_codec("ogg", "mkv") is True

    def test_mka_can_copy(self):
        """Test that MKA can copy codec."""
        assert can_copy_codec("mp3", "mka") is True

    def test_ts_to_mp3_can_copy(self):
        """Test that TS to MP3 can copy."""
        assert can_copy_codec("ts", "mp3") is True

    def test_mp3_to_m4b_cannot_copy(self):
        """Test that MP3 to M4B cannot copy codec."""
        assert can_copy_codec("mp3", "m4b") is False

    def test_same_format_cannot_copy(self):
        """Test that same formats don't trigger copy (will be skipped)."""
        assert can_copy_codec("mp3", "mp3") is False
        assert can_copy_codec("m4b", "m4b") is False


class TestCheckEncoderAvailable:
    """Tests for check_encoder_available function."""

    @patch("subprocess.run")
    def test_encoder_available(self, mock_run):
        """Test detecting available encoder."""
        mock_run.return_value = Mock(
            stdout=" A..... aac                  AAC (Advanced Audio Coding)\n A..... libfdk_aac",
            returncode=0,
        )

        assert check_encoder_available("aac") is True
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_encoder_not_available(self, mock_run):
        """Test detecting unavailable encoder."""
        mock_run.return_value = Mock(
            stdout=" A..... aac                  AAC (Advanced Audio Coding)\n",
            returncode=0,
        )

        assert check_encoder_available("libfdk_aac") is False

    @patch("subprocess.run")
    def test_ffmpeg_not_found(self, mock_run):
        """Test handling when FFmpeg is not installed."""
        mock_run.side_effect = FileNotFoundError()

        assert check_encoder_available("aac") is False

    @patch("subprocess.run")
    def test_ffmpeg_timeout(self, mock_run):
        """Test handling FFmpeg timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ffmpeg", timeout=5)

        assert check_encoder_available("aac") is False


class TestGetAudioBitrate:
    """Tests for get_audio_bitrate function."""

    @patch("subprocess.run")
    def test_get_bitrate_from_file(self, mock_run):
        """Test extracting audio bitrate from file."""
        mock_run.return_value = Mock(
            stdout='{"streams": [{"bit_rate": "128000"}]}',
            returncode=0,
        )

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate == 128

    @patch("subprocess.run")
    def test_get_high_bitrate(self, mock_run):
        """Test extracting high bitrate."""
        mock_run.return_value = Mock(
            stdout='{"streams": [{"bit_rate": "320000"}]}',
            returncode=0,
        )

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate == 320

    @patch("subprocess.run")
    def test_bitrate_missing_from_stream(self, mock_run):
        """Test handling missing bitrate information."""
        mock_run.return_value = Mock(
            stdout='{"streams": [{"codec_name": "mp3"}]}',
            returncode=0,
        )

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate is None

    @patch("subprocess.run")
    def test_empty_streams(self, mock_run):
        """Test handling empty streams."""
        mock_run.return_value = Mock(
            stdout='{"streams": []}',
            returncode=0,
        )

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate is None

    @patch("subprocess.run")
    def test_ffprobe_not_found(self, mock_run):
        """Test handling when ffprobe is not installed."""
        mock_run.side_effect = FileNotFoundError()

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate is None

    @patch("subprocess.run")
    def test_invalid_json(self, mock_run):
        """Test handling invalid JSON from ffprobe."""
        mock_run.return_value = Mock(
            stdout='not valid json',
            returncode=0,
        )

        bitrate = get_audio_bitrate("/path/to/audio.mp3")
        assert bitrate is None


class TestRemoveChars:
    """Tests for _remove_chars function."""

    def test_remove_single_char(self):
        """Test removing a single character."""
        result = _remove_chars("hello:world", ":")
        assert result == "helloworld"

    def test_remove_multiple_chars(self):
        """Test removing multiple characters."""
        result = _remove_chars("file:name*with?bad<chars>", ":*?<>")
        assert result == "filenamewithbadchars"

    def test_remove_no_chars(self):
        """Test with empty remove string."""
        result = _remove_chars("filename", "")
        assert result == "filename"

    def test_remove_none_chars(self):
        """Test with None remove parameter."""
        result = _remove_chars("filename", None)
        assert result == "filename"

    def test_remove_repeated_chars(self):
        """Test removing repeated characters."""
        result = _remove_chars("a::b::c", ":")
        assert result == "abc"

    def test_remove_unicode_chars(self):
        """Test removing unicode characters."""
        result = _remove_chars("hello™world®", "™®")
        assert result == "helloworld"


class TestFixOutput:
    """Tests for _fix_output function."""

    def test_fix_forward_slash(self):
        """Test that forward slashes are replaced with hyphens."""
        result = _fix_output("Book 1/Chapter 1")
        assert result == "Book 1-Chapter 1"
        assert "/" not in result

    @patch("platform.system")
    def test_fix_windows_invalid_chars(self, mock_system):
        """Test removing Windows-specific invalid characters."""
        mock_system.return_value = "Windows"

        result = _fix_output('file:name*with?bad<chars>|"test"')
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    @patch("platform.system")
    def test_fix_unix_keeps_most_chars(self, mock_system):
        """Test that Unix systems only fix forward slashes."""
        mock_system.return_value = "Linux"

        result = _fix_output("file:name*with?chars")
        assert "/" not in result
        # Unix allows these characters in filenames
        assert ":" in result
        assert "*" in result
        assert "?" in result

    def test_fix_multiple_slashes(self):
        """Test fixing multiple forward slashes."""
        result = _fix_output("path/to/some/file")
        assert result == "path-to-some-file"


class TestGetMaxNameLength:
    """Tests for get_max_name_length function."""

    @patch("os.pathconf")
    def test_get_name_length_unix(self, mock_pathconf):
        """Test getting max name length on Unix systems."""
        mock_pathconf.return_value = 255

        assert get_max_name_length() == 255
        mock_pathconf.assert_called_once_with(".", "PC_NAME_MAX")

    @patch("os.pathconf")
    def test_get_name_length_default(self, mock_pathconf):
        """Test default name length when detection fails."""
        mock_pathconf.side_effect = Exception()

        # Should return default value
        length = get_max_name_length()
        assert isinstance(length, int)
        assert length >= 255


class TestGenOutputLocation:
    """Tests for gen_output_location function."""

    def test_basic_template(self, sample_metadata):
        """Test basic template with author and title."""
        template = "{author}/{title}"

        result = gen_output_location(template, sample_metadata, None)

        assert "F. Scott Fitzgerald" in result
        assert "The Great Gatsby" in result

    def test_template_with_narrator(self, sample_metadata):
        """Test template including narrator."""
        template = "{narrator} - {title}"

        result = gen_output_location(template, sample_metadata, None)

        assert "Jake Gyllenhaal" in result
        assert "The Great Gatsby" in result

    def test_template_with_series(self, sample_metadata):
        """Test template with series information."""
        template = "{series}/{series_order} - {title}"

        result = gen_output_location(template, sample_metadata, None)

        assert "Great American Novels" in result
        assert "1" in result

    def test_remove_chars_from_metadata(self, sample_metadata):
        """Test that remove_chars is applied to metadata values."""
        template = "{author}/{title}"
        sample_metadata.title = "Book:Title*With?Invalid<Chars>"

        result = gen_output_location(template, sample_metadata, ":*?<>")

        assert "BookTitleWithInvalidChars" in result
        assert ":" not in result.split("/")[-1]

    def test_long_title_truncation(self, sample_metadata):
        """Test that very long titles are truncated."""
        # Create a very long title
        sample_metadata.title = "A" * 300

        template = "{title}"
        result = gen_output_location(template, sample_metadata, None)

        # Should be truncated to fit max filename length
        assert len(result.encode('utf-8')) < 255

    def test_fallback_to_narrator_for_author(self, minimal_metadata):
        """Test that narrator is used when author is missing."""
        minimal_metadata.narrators = ["Narrator Name"]
        template = "{author}"

        result = gen_output_location(template, minimal_metadata, None)

        assert "Narrator Name" in result

    def test_tilde_expansion(self, sample_metadata):
        """Test that ~ is expanded to home directory."""
        template = "~/audiobooks/{title}"

        result = gen_output_location(template, sample_metadata, None)

        # Tilde should be expanded
        assert not result.startswith("~")
        assert "audiobooks" in result

    def test_default_values_used(self, minimal_metadata):
        """Test that default values are used for missing metadata."""
        template = "{artist}/{album}"

        result = gen_output_location(template, minimal_metadata, None)

        # Should use defaults for artist/album
        assert "NA" in result


class TestCombineAudiofiles:
    """Tests for combine_audiofiles function."""

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    @patch("os.path.exists")
    def test_combine_two_files_debug_mode(self, mock_exists, mock_logging, mock_run, temp_dir):
        """Test combining two files in debug mode."""
        mock_logging.ffmpeg_output = True
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = True

        # Create test files
        file1 = temp_dir / "part1.mp3"
        file2 = temp_dir / "part2.mp3"
        file1.write_bytes(b"audio1")
        file2.write_bytes(b"audio2")

        output_path = str(temp_dir / "combined.mp3")
        filepaths = [str(file1), str(file2)]

        # Need to create tmp files for the function
        with patch("shutil.move"), patch("shutil.rmtree"), patch("os.remove"):
            combine_audiofiles(filepaths, str(temp_dir), output_path)

        # FFmpeg should have been called
        assert mock_run.called

    @patch("audiobookdl.output.output.run_ffmpeg_with_progress")
    @patch("audiobookdl.output.output.get_media_duration")
    @patch("audiobookdl.output.output.logging")
    @patch("os.path.exists")
    def test_combine_multiple_files(self, mock_exists, mock_logging, mock_duration, mock_ffmpeg, temp_dir):
        """Test combining multiple files with progress tracking."""
        mock_logging.ffmpeg_output = False
        mock_duration.return_value = 100.0
        mock_ffmpeg.return_value = (0, "", "")
        mock_exists.return_value = True

        # Create test files
        files = []
        for i in range(5):
            f = temp_dir / f"part{i}.mp3"
            f.write_bytes(b"audio")
            files.append(str(f))

        output_path = str(temp_dir / "combined.mp3")

        # Mock progress context
        mock_progress = MagicMock()
        mock_logging.progress.return_value.__enter__.return_value = mock_progress
        mock_logging.progress.return_value.__exit__.return_value = None

        with patch("shutil.move"), patch("shutil.rmtree"), patch("os.remove"):
            combine_audiofiles(files, str(temp_dir), output_path)

        # Progress tracking should be used
        assert mock_progress.add_task.called

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    @patch("os.path.exists")
    def test_combine_fails_raises_exception(self, mock_exists, mock_logging, mock_run, temp_dir):
        """Test that combining failure raises CalledProcessError."""
        mock_logging.ffmpeg_output = True
        mock_run.return_value = Mock(returncode=1)
        mock_exists.return_value = True

        file1 = temp_dir / "part1.mp3"
        file1.write_bytes(b"audio")

        output_path = str(temp_dir / "combined.mp3")

        with patch("shutil.move"), patch("os.remove"):
            with pytest.raises(subprocess.CalledProcessError):
                combine_audiofiles([str(file1)], str(temp_dir), output_path)

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    @patch("os.path.exists")
    def test_combine_missing_output_raises_failed_combining(self, mock_exists, mock_logging, mock_run, temp_dir):
        """Test that missing output file raises FailedCombining."""
        mock_logging.ffmpeg_output = True
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = False  # Output doesn't exist

        file1 = temp_dir / "part1.mp3"
        file1.write_bytes(b"audio")

        output_path = str(temp_dir / "combined.mp3")

        with patch("shutil.move"), patch("shutil.rmtree"), patch("os.remove"):
            with pytest.raises(FailedCombining):
                combine_audiofiles([str(file1)], str(temp_dir), output_path)


class TestConvertOutput:
    """Tests for convert_output function."""

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    def test_convert_single_file_codec_copy(self, mock_logging, mock_run, temp_dir):
        """Test converting with codec copy (no re-encoding)."""
        mock_logging.ffmpeg_output = True
        mock_run.return_value = Mock(returncode=0)

        # Create test file
        input_file = temp_dir / "audio.ts"
        input_file.write_bytes(b"audio data")

        with patch("os.remove"):
            result = convert_output([str(input_file)], "mp3", None)

        # Should use codec copy
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "-codec" in call_args or "-c" in call_args
        assert "copy" in call_args

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.check_encoder_available")
    @patch("audiobookdl.output.output.get_audio_bitrate")
    @patch("audiobookdl.output.output.logging")
    def test_convert_to_m4b_with_encoder(self, mock_logging, mock_bitrate, mock_encoder, mock_run, temp_dir):
        """Test converting to M4B with AAC encoder."""
        mock_logging.ffmpeg_output = True
        mock_encoder.return_value = True
        mock_bitrate.return_value = 128
        mock_run.return_value = Mock(returncode=0)

        input_file = temp_dir / "audio.mp3"
        input_file.write_bytes(b"audio")

        with patch("os.remove"):
            result = convert_output([str(input_file)], "m4b", "aac")

        # Should check encoder availability
        mock_encoder.assert_called_with("aac")

        # Should use AAC encoder with bitrate
        call_args = mock_run.call_args[0][0]
        assert "aac" in call_args
        assert "128k" in call_args

    @patch("audiobookdl.output.output.check_encoder_available")
    @patch("audiobookdl.output.output.logging")
    def test_convert_missing_encoder_raises(self, mock_logging, mock_encoder, temp_dir):
        """Test that missing encoder raises MissingEncoder."""
        mock_logging.ffmpeg_output = True
        mock_encoder.return_value = False

        input_file = temp_dir / "audio.mp3"
        input_file.write_bytes(b"audio")

        with pytest.raises(MissingEncoder):
            convert_output([str(input_file)], "m4b", "libfdk_aac")

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    def test_convert_same_format_skipped(self, mock_logging, mock_run, temp_dir):
        """Test that conversion is skipped for same format."""
        mock_logging.ffmpeg_output = True

        input_file = temp_dir / "audio.mp3"
        input_file.write_bytes(b"audio")

        result = convert_output([str(input_file)], "mp3", None)

        # No conversion should happen
        assert not mock_run.called
        assert str(input_file) in result

    @patch("audiobookdl.output.output.run_ffmpeg_with_progress")
    @patch("audiobookdl.output.output.get_media_duration")
    @patch("audiobookdl.output.output.check_encoder_available")
    @patch("audiobookdl.output.output.logging")
    def test_convert_multiple_files(self, mock_logging, mock_encoder, mock_duration, mock_ffmpeg, temp_dir):
        """Test converting multiple files with progress."""
        mock_logging.ffmpeg_output = False
        mock_encoder.return_value = True
        mock_duration.return_value = 100.0
        mock_ffmpeg.return_value = (0, "", "")

        files = []
        for i in range(3):
            f = temp_dir / f"audio{i}.mp3"
            f.write_bytes(b"audio")
            files.append(str(f))

        mock_progress = MagicMock()
        mock_logging.progress.return_value.__enter__.return_value = mock_progress
        mock_logging.progress.return_value.__exit__.return_value = None

        with patch("os.remove"):
            result = convert_output(files, "m4b", "aac")

        # Should convert all files
        assert len(result) == 3
        assert all(f.endswith(".m4b") for f in result)

    @patch("audiobookdl.output.output.subprocess.run")
    @patch("audiobookdl.output.output.logging")
    def test_convert_failure_raises_exception(self, mock_logging, mock_run, temp_dir):
        """Test that conversion failure raises CalledProcessError."""
        mock_logging.ffmpeg_output = True
        mock_run.return_value = Mock(returncode=1)

        input_file = temp_dir / "audio.mp3"
        input_file.write_bytes(b"audio")

        with pytest.raises(subprocess.CalledProcessError):
            convert_output([str(input_file)], "m4b", "aac")
