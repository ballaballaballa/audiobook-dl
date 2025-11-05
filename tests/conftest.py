"""
Pytest configuration and shared fixtures for audiobook-dl tests.
"""
import pytest
import requests
import tempfile
from pathlib import Path
from datetime import date
from typing import List
import pycountry

from audiobookdl.utils.audiobook import (
    Audiobook,
    AudiobookFile,
    AudiobookMetadata,
    Chapter,
    Cover,
    AESEncryption,
    Series,
    BookId,
)


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def mock_session():
    """Provide a mock requests session."""
    return requests.Session()


@pytest.fixture
def sample_cover() -> Cover:
    """Provide sample cover image data."""
    # 1x1 red PNG (smallest valid PNG)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03'
        b'\x00\x01\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return Cover(image=png_data, extension="png")


@pytest.fixture
def sample_cover_jpeg() -> Cover:
    """Provide sample JPEG cover image data."""
    # 1x1 red JPEG (smallest valid JPEG)
    jpeg_data = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01'
        b'\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06'
        b'\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b'
        b'\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c'
        b'\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff'
        b'\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff'
        b'\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\x00\x00\x00\x00\t\xff\xc4\x00\x14\x10\x01'
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00T\xdf'
        b'\xff\xd9'
    )
    return Cover(image=jpeg_data, extension="jpg")


@pytest.fixture
def sample_metadata() -> AudiobookMetadata:
    """Provide sample audiobook metadata."""
    metadata = AudiobookMetadata(
        title="The Great Gatsby",
        authors=["F. Scott Fitzgerald"],
        narrators=["Jake Gyllenhaal"],
        genres=["Fiction", "Classics"],
        language=pycountry.languages.get(alpha_3="eng"),
        description="A classic American novel set in the Jazz Age.",
        isbn="9780743273565",
        publisher="Scribner",
        release_date=date(1925, 4, 10),
        series="Great American Novels",
        series_order=1,
        scrape_url="https://example.com/audiobooks/great-gatsby",
    )
    return metadata


@pytest.fixture
def minimal_metadata() -> AudiobookMetadata:
    """Provide minimal audiobook metadata with only required fields."""
    return AudiobookMetadata(title="Test Audiobook")


@pytest.fixture
def sample_chapters() -> List[Chapter]:
    """Provide sample chapter data."""
    return [
        Chapter(start=0, title="Chapter 1: The Beginning"),
        Chapter(start=300000, title="Chapter 2: The Middle"),
        Chapter(start=600000, title="Chapter 3: The End"),
    ]


@pytest.fixture
def sample_audiobook_file() -> AudiobookFile:
    """Provide a sample audiobook file."""
    return AudiobookFile(
        url="https://example.com/audiobook/part1.mp3",
        ext="mp3",
        title="Part 1",
        headers={"User-Agent": "audiobook-dl/test"},
    )


@pytest.fixture
def sample_audiobook_files() -> List[AudiobookFile]:
    """Provide multiple sample audiobook files."""
    return [
        AudiobookFile(
            url=f"https://example.com/audiobook/part{i}.mp3",
            ext="mp3",
            title=f"Part {i}",
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def encrypted_audiobook_file() -> AudiobookFile:
    """Provide an encrypted audiobook file."""
    encryption = AESEncryption(
        key=b"0123456789abcdef",
        iv=b"fedcba9876543210",
    )
    return AudiobookFile(
        url="https://example.com/encrypted/part1.mp3",
        ext="mp3",
        title="Encrypted Part 1",
        encryption_method=encryption,
    )


@pytest.fixture
def sample_audiobook(mock_session, sample_metadata, sample_audiobook_files, sample_chapters, sample_cover) -> Audiobook:
    """Provide a complete sample audiobook."""
    return Audiobook(
        session=mock_session,
        metadata=sample_metadata,
        files=sample_audiobook_files,
        chapters=sample_chapters,
        cover=sample_cover,
    )


@pytest.fixture
def minimal_audiobook(mock_session, minimal_metadata, sample_audiobook_file) -> Audiobook:
    """Provide a minimal audiobook with only required fields."""
    return Audiobook(
        session=mock_session,
        metadata=minimal_metadata,
        files=[sample_audiobook_file],
    )


@pytest.fixture
def sample_series(sample_metadata) -> Series:
    """Provide a sample series."""
    return Series(
        title="Great American Novels",
        books=[
            BookId(id="book1"),
            BookId(id="book2"),
            BookId(id="book3"),
        ],
    )


@pytest.fixture
def aes_encryption() -> AESEncryption:
    """Provide sample AES encryption data."""
    return AESEncryption(
        key=b"0123456789abcdef",
        iv=b"fedcba9876543210",
    )


@pytest.fixture
def sample_audio_file_path(temp_dir) -> Path:
    """Create a sample audio file for testing."""
    # Create a minimal valid MP3 file (just headers, no actual audio)
    audio_file = temp_dir / "test.mp3"
    # ID3v2 header + minimal MP3 frame
    mp3_data = (
        b'ID3\x04\x00\x00\x00\x00\x00\x00'  # ID3v2.4 header
        b'\xff\xfb\x90\x00'  # MP3 frame sync
    )
    audio_file.write_bytes(mp3_data)
    return audio_file


@pytest.fixture
def sample_m3u8_playlist() -> str:
    """Provide a sample M3U8 playlist content."""
    return """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
segment0.ts
#EXTINF:10.0,
segment1.ts
#EXTINF:10.0,
segment2.ts
#EXT-X-ENDLIST
"""


@pytest.fixture
def sample_encrypted_m3u8_playlist() -> str:
    """Provide a sample encrypted M3U8 playlist with AES-128."""
    return """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-KEY:METHOD=AES-128,URI="https://example.com/key.bin",IV=0x12345678901234567890123456789012
#EXTINF:10.0,
segment0.ts
#EXTINF:10.0,
segment1.ts
#EXTINF:10.0,
segment2.ts
#EXT-X-ENDLIST
"""


@pytest.fixture
def mock_config_dict():
    """Provide a mock configuration dictionary."""
    return {
        "output": "{author}/{title}",
        "output_format": "m4b",
        "combine": True,
        "sources": {
            "storytel": {
                "username": "test@example.com",
                "password": "testpassword",
            },
            "nextory": {
                "cookies": "tests/fixtures/cookies.txt",
            },
        },
    }


@pytest.fixture
def sample_cookies_txt(temp_dir) -> Path:
    """Create a sample Netscape cookies.txt file."""
    cookies_file = temp_dir / "cookies.txt"
    cookies_content = """# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.example.com\tTRUE\t/\tFALSE\t1234567890\tsession_id\tabc123
.example.com\tTRUE\t/\tFALSE\t1234567890\tauth_token\tdef456
"""
    cookies_file.write_text(cookies_content)
    return cookies_file


@pytest.fixture
def sample_html_page() -> str:
    """Provide sample HTML page content for parsing tests."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Audiobook</title>
</head>
<body>
    <div class="audiobook-info">
        <h1 class="title">The Great Gatsby</h1>
        <p class="author">F. Scott Fitzgerald</p>
        <p class="narrator">Jake Gyllenhaal</p>
        <div class="description">
            A classic American novel set in the Jazz Age.
        </div>
        <span class="isbn">9780743273565</span>
    </div>
    <div class="audio-files">
        <a href="/files/part1.mp3" class="download-link">Part 1</a>
        <a href="/files/part2.mp3" class="download-link">Part 2</a>
        <a href="/files/part3.mp3" class="download-link">Part 3</a>
    </div>
</body>
</html>
"""


@pytest.fixture
def sample_json_metadata() -> dict:
    """Provide sample JSON metadata for API response tests."""
    return {
        "title": "The Great Gatsby",
        "authors": ["F. Scott Fitzgerald"],
        "narrators": ["Jake Gyllenhaal"],
        "genres": ["Fiction", "Classics"],
        "language": "eng",
        "description": "A classic American novel set in the Jazz Age.",
        "isbn": "9780743273565",
        "publisher": "Scribner",
        "release_date": "1925-04-10",
        "files": [
            {"url": "https://example.com/part1.mp3", "title": "Part 1"},
            {"url": "https://example.com/part2.mp3", "title": "Part 2"},
            {"url": "https://example.com/part3.mp3", "title": "Part 3"},
        ],
    }
