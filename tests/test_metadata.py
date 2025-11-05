"""
Tests for metadata writing functionality in audiobook-dl.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path

from audiobookdl.output.metadata import add_metadata, embed_cover, add_chapters
from audiobookdl.utils.audiobook import AudiobookMetadata, Chapter, Cover


class TestAddMetadata:
    """Tests for add_metadata function."""

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_metadata_to_mp3(self, mock_is_id3, mock_add_id3, sample_metadata):
        """Test adding metadata to MP3 file."""
        mock_is_id3.return_value = True

        add_metadata("test.mp3", sample_metadata)

        mock_is_id3.assert_called_once_with("test.mp3")
        mock_add_id3.assert_called_once_with("test.mp3", sample_metadata)

    @patch("audiobookdl.output.metadata.mp4.add_mp4_metadata")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_metadata_to_m4b(self, mock_is_id3, mock_is_mp4, mock_add_mp4, sample_metadata):
        """Test adding metadata to M4B file."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = True

        add_metadata("test.m4b", sample_metadata)

        mock_is_mp4.assert_called_once_with("test.m4b")
        mock_add_mp4.assert_called_once_with("test.m4b", sample_metadata)

    @patch("audiobookdl.output.metadata.logging")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_metadata_unsupported_format(self, mock_is_id3, mock_is_mp4, mock_logging, sample_metadata):
        """Test handling unsupported file format."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = False

        add_metadata("test.ogg", sample_metadata)

        # Should log debug message
        mock_logging.debug.assert_called_once()

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_minimal_metadata(self, mock_is_id3, mock_add_id3, minimal_metadata):
        """Test adding minimal metadata (title only)."""
        mock_is_id3.return_value = True

        add_metadata("test.mp3", minimal_metadata)

        mock_add_id3.assert_called_once_with("test.mp3", minimal_metadata)


class TestEmbedCover:
    """Tests for embed_cover function."""

    @patch("audiobookdl.output.metadata.id3.embed_id3_cover")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_cover_to_mp3(self, mock_is_id3, mock_embed_id3, sample_cover):
        """Test embedding cover to MP3 file."""
        mock_is_id3.return_value = True

        embed_cover("test.mp3", sample_cover)

        mock_is_id3.assert_called_once_with("test.mp3")
        mock_embed_id3.assert_called_once_with("test.mp3", sample_cover)

    @patch("audiobookdl.output.metadata.mp4.embed_mp4_cover")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_cover_to_m4b(self, mock_is_id3, mock_is_mp4, mock_embed_mp4, sample_cover):
        """Test embedding cover to M4B file."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = True

        embed_cover("test.m4b", sample_cover)

        mock_is_mp4.assert_called_once_with("test.m4b")
        mock_embed_mp4.assert_called_once_with("test.m4b", sample_cover)

    @patch("audiobookdl.output.metadata.id3.embed_id3_cover")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_png_cover(self, mock_is_id3, mock_embed_id3, sample_cover):
        """Test embedding PNG cover image."""
        mock_is_id3.return_value = True

        embed_cover("test.mp3", sample_cover)

        # Verify cover object has correct extension
        called_cover = mock_embed_id3.call_args[0][1]
        assert called_cover.extension == "png"

    @patch("audiobookdl.output.metadata.id3.embed_id3_cover")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_jpeg_cover(self, mock_is_id3, mock_embed_id3, sample_cover_jpeg):
        """Test embedding JPEG cover image."""
        mock_is_id3.return_value = True

        embed_cover("test.mp3", sample_cover_jpeg)

        called_cover = mock_embed_id3.call_args[0][1]
        assert called_cover.extension == "jpg"

    @patch("audiobookdl.output.metadata.logging")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_cover_unsupported_format(self, mock_is_id3, mock_is_mp4, mock_logging, sample_cover):
        """Test embedding cover to unsupported format."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = False

        embed_cover("test.ogg", sample_cover)

        # Should log debug message
        mock_logging.debug.assert_called_once()


class TestAddChapters:
    """Tests for add_chapters function."""

    @patch("audiobookdl.output.metadata.id3.add_id3_chapters")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_chapters_to_mp3(self, mock_is_id3, mock_add_id3_chapters, sample_chapters):
        """Test adding chapters to MP3 file."""
        mock_is_id3.return_value = True

        add_chapters("test.mp3", sample_chapters)

        mock_is_id3.assert_called_once_with("test.mp3")
        mock_add_id3_chapters.assert_called_once_with("test.mp3", sample_chapters)

    @patch("audiobookdl.output.metadata.ffmpeg.add_chapters_ffmpeg")
    @patch("audiobookdl.output.metadata.program_in_path")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_chapters_to_m4b_with_ffmpeg(self, mock_is_id3, mock_program_in_path, mock_add_ffmpeg, sample_chapters):
        """Test adding chapters to M4B using ffmpeg."""
        mock_is_id3.return_value = False
        mock_program_in_path.return_value = True

        add_chapters("test.m4b", sample_chapters)

        mock_program_in_path.assert_called_once_with("ffmpeg")
        mock_add_ffmpeg.assert_called_once_with("test.m4b", sample_chapters)

    @patch("audiobookdl.output.metadata.logging")
    @patch("audiobookdl.output.metadata.program_in_path")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_chapters_without_ffmpeg(self, mock_is_id3, mock_program_in_path, mock_logging, sample_chapters):
        """Test adding chapters when ffmpeg is not available."""
        mock_is_id3.return_value = False
        mock_program_in_path.return_value = False
        mock_logging.debug_mode = False

        add_chapters("test.m4b", sample_chapters)

        # Should call print_error_file
        mock_logging.print_error_file.assert_called_once()

    def test_add_empty_chapters_list(self):
        """Test adding empty chapters list."""
        with patch("audiobookdl.output.metadata.id3.is_id3_file") as mock_is_id3:
            with patch("audiobookdl.output.metadata.id3.add_id3_chapters") as mock_add:
                mock_is_id3.return_value = True

                add_chapters("test.mp3", [])

                # Should still call the function even with empty list
                mock_add.assert_called_once_with("test.mp3", [])

    @patch("audiobookdl.output.metadata.id3.add_id3_chapters")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_chapters_with_different_start_times(self, mock_is_id3, mock_add, sample_chapters):
        """Test adding chapters with various start times."""
        mock_is_id3.return_value = True

        chapters = [
            Chapter(start=0, title="Prologue"),
            Chapter(start=5000, title="Chapter 1"),
            Chapter(start=600000, title="Chapter 2"),
            Chapter(start=3600000, title="Epilogue"),
        ]

        add_chapters("test.mp3", chapters)

        called_chapters = mock_add.call_args[0][1]
        assert len(called_chapters) == 4
        assert called_chapters[0].start == 0
        assert called_chapters[-1].start == 3600000


class TestMetadataIntegration:
    """Integration tests for metadata functions working together."""

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.embed_id3_cover")
    @patch("audiobookdl.output.metadata.id3.add_id3_chapters")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_all_metadata_to_mp3(
        self,
        mock_is_id3,
        mock_add_chapters,
        mock_embed_cover,
        mock_add_metadata,
        sample_metadata,
        sample_cover,
        sample_chapters
    ):
        """Test adding all metadata types to MP3 file."""
        mock_is_id3.return_value = True

        add_metadata("test.mp3", sample_metadata)
        embed_cover("test.mp3", sample_cover)
        add_chapters("test.mp3", sample_chapters)

        # All functions should be called
        mock_add_metadata.assert_called_once()
        mock_embed_cover.assert_called_once()
        mock_add_chapters.assert_called_once()

    @patch("audiobookdl.output.metadata.mp4.add_mp4_metadata")
    @patch("audiobookdl.output.metadata.mp4.embed_mp4_cover")
    @patch("audiobookdl.output.metadata.ffmpeg.add_chapters_ffmpeg")
    @patch("audiobookdl.output.metadata.program_in_path")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_add_all_metadata_to_m4b(
        self,
        mock_is_id3,
        mock_is_mp4,
        mock_program_in_path,
        mock_add_chapters,
        mock_embed_cover,
        mock_add_metadata,
        sample_metadata,
        sample_cover,
        sample_chapters
    ):
        """Test adding all metadata types to M4B file."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = True
        mock_program_in_path.return_value = True

        add_metadata("test.m4b", sample_metadata)
        embed_cover("test.m4b", sample_cover)
        add_chapters("test.m4b", sample_chapters)

        # All functions should be called
        mock_add_metadata.assert_called_once()
        mock_embed_cover.assert_called_once()
        mock_add_chapters.assert_called_once()


class TestMetadataFileTypeDetection:
    """Tests for file type detection in metadata module."""

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_mp3_file_detected(self, mock_is_id3, mock_add, sample_metadata):
        """Test that .mp3 files are detected correctly."""
        mock_is_id3.return_value = True

        add_metadata("audiobook.mp3", sample_metadata)

        mock_is_id3.assert_called_with("audiobook.mp3")
        mock_add.assert_called_once()

    @patch("audiobookdl.output.metadata.mp4.add_mp4_metadata")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_m4b_file_detected(self, mock_is_id3, mock_is_mp4, mock_add, sample_metadata):
        """Test that .m4b files are detected correctly."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = True

        add_metadata("audiobook.m4b", sample_metadata)

        mock_is_mp4.assert_called_with("audiobook.m4b")
        mock_add.assert_called_once()

    @patch("audiobookdl.output.metadata.mp4.add_mp4_metadata")
    @patch("audiobookdl.output.metadata.mp4.is_mp4_file")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_m4a_file_detected(self, mock_is_id3, mock_is_mp4, mock_add, sample_metadata):
        """Test that .m4a files are detected correctly."""
        mock_is_id3.return_value = False
        mock_is_mp4.return_value = True

        add_metadata("audiobook.m4a", sample_metadata)

        mock_is_mp4.assert_called_with("audiobook.m4a")
        mock_add.assert_called_once()


class TestMetadataEdgeCases:
    """Tests for edge cases in metadata handling."""

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_metadata_with_unicode_title(self, mock_is_id3, mock_add):
        """Test metadata with Unicode characters in title."""
        mock_is_id3.return_value = True

        metadata = AudiobookMetadata(
            title="日本語のタイトル (Japanese Title)",
            authors=["著者"],
        )

        add_metadata("test.mp3", metadata)

        called_metadata = mock_add.call_args[0][1]
        assert "日本語" in called_metadata.title
        assert "著者" in called_metadata.authors[0]

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_metadata_with_special_characters(self, mock_is_id3, mock_add):
        """Test metadata with special characters."""
        mock_is_id3.return_value = True

        metadata = AudiobookMetadata(
            title="Title: With <Special> & 'Characters' \"Test\"",
            authors=["O'Brien, Patrick"],
        )

        add_metadata("test.mp3", metadata)

        called_metadata = mock_add.call_args[0][1]
        assert ":" in called_metadata.title
        assert "&" in called_metadata.title
        assert "'" in called_metadata.authors[0]

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_metadata_with_very_long_title(self, mock_is_id3, mock_add):
        """Test metadata with very long title."""
        mock_is_id3.return_value = True

        long_title = "A" * 500
        metadata = AudiobookMetadata(title=long_title)

        add_metadata("test.mp3", metadata)

        called_metadata = mock_add.call_args[0][1]
        # Title should be preserved (truncation happens at path level, not metadata)
        assert len(called_metadata.title) == 500

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_metadata_with_multiple_authors(self, mock_is_id3, mock_add):
        """Test metadata with multiple authors."""
        mock_is_id3.return_value = True

        metadata = AudiobookMetadata(
            title="Collaborative Work",
            authors=["Author One", "Author Two", "Author Three"],
        )

        add_metadata("test.mp3", metadata)

        called_metadata = mock_add.call_args[0][1]
        assert len(called_metadata.authors) == 3

    @patch("audiobookdl.output.metadata.id3.add_id3_metadata")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_metadata_with_multiple_narrators(self, mock_is_id3, mock_add):
        """Test metadata with multiple narrators."""
        mock_is_id3.return_value = True

        metadata = AudiobookMetadata(
            title="Multi-narrator Audiobook",
            narrators=["Narrator A", "Narrator B"],
        )

        add_metadata("test.mp3", metadata)

        called_metadata = mock_add.call_args[0][1]
        assert len(called_metadata.narrators) == 2

    @patch("audiobookdl.output.metadata.id3.add_id3_chapters")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_chapters_with_zero_duration(self, mock_is_id3, mock_add):
        """Test chapters where some have zero duration (sequential)."""
        mock_is_id3.return_value = True

        chapters = [
            Chapter(start=0, title="Start"),
            Chapter(start=0, title="Duplicate Start"),
            Chapter(start=1000, title="Next"),
        ]

        add_chapters("test.mp3", chapters)

        # Should handle duplicate start times
        called_chapters = mock_add.call_args[0][1]
        assert len(called_chapters) == 3

    @patch("audiobookdl.output.metadata.id3.embed_id3_cover")
    @patch("audiobookdl.output.metadata.id3.is_id3_file")
    def test_embed_large_cover_image(self, mock_is_id3, mock_embed):
        """Test embedding large cover image."""
        mock_is_id3.return_value = True

        # Create a "large" cover (simulated)
        large_image_data = b"\x00" * (5 * 1024 * 1024)  # 5MB
        cover = Cover(image=large_image_data, extension="jpg")

        embed_cover("test.mp3", cover)

        called_cover = mock_embed.call_args[0][1]
        assert len(called_cover.image) == 5 * 1024 * 1024


class TestChapterStructure:
    """Tests for chapter data structure."""

    def test_chapter_creation(self):
        """Test creating a chapter object."""
        chapter = Chapter(start=5000, title="Chapter 1")

        assert chapter.start == 5000
        assert chapter.title == "Chapter 1"

    def test_chapter_zero_start(self):
        """Test chapter starting at zero."""
        chapter = Chapter(start=0, title="Prologue")

        assert chapter.start == 0

    def test_chapter_large_start_time(self):
        """Test chapter with large start time (long audiobook)."""
        # 10 hours in milliseconds
        chapter = Chapter(start=36000000, title="Final Chapter")

        assert chapter.start == 36000000

    def test_chapter_unicode_title(self):
        """Test chapter with Unicode title."""
        chapter = Chapter(start=1000, title="第一章")

        assert "第一章" in chapter.title

    def test_multiple_chapters_ordering(self, sample_chapters):
        """Test that chapters maintain order."""
        assert sample_chapters[0].start < sample_chapters[1].start
        assert sample_chapters[1].start < sample_chapters[2].start


class TestCoverStructure:
    """Tests for cover image data structure."""

    def test_cover_png_creation(self, sample_cover):
        """Test creating PNG cover."""
        assert sample_cover.extension == "png"
        assert isinstance(sample_cover.image, bytes)
        assert len(sample_cover.image) > 0

    def test_cover_jpeg_creation(self, sample_cover_jpeg):
        """Test creating JPEG cover."""
        assert sample_cover_jpeg.extension == "jpg"
        assert isinstance(sample_cover_jpeg.image, bytes)

    def test_cover_has_valid_image_data(self, sample_cover):
        """Test that cover has valid image header."""
        # PNG signature
        assert sample_cover.image[:8] == b'\x89PNG\r\n\x1a\n'

    def test_cover_jpeg_has_valid_header(self, sample_cover_jpeg):
        """Test that JPEG cover has valid header."""
        # JPEG signature
        assert sample_cover_jpeg.image[:2] == b'\xff\xd8'
