"""
Tests for URL matching to source implementations.
"""
import pytest
from audiobookdl.sources import find_compatible_source, get_source_names
from audiobookdl.exceptions import NoSourceFound


# Test data: URL -> Expected Source Name
TEST_DATA = {
    # Audiobooks.com
    "https://www.audiobooks.com/book/stream/413879": "Audiobooksdotcom",
    "https://www.audiobooks.com/browse/library": "Audiobooksdotcom",
    "https://www.audiobooks.com/audiobook/title-here/123456": "Audiobooksdotcom",

    # Blinkist
    "https://www.blinkist.com/en/nc/reader/book-title-here": "Blinkist",
    "https://www.blinkist.com/en/books/book-name-en": "Blinkist",

    # BookBeat
    "https://www.bookbeat.no/bok/somethingsomething-999999": "BookBeat",
    "https://www.bookbeat.com/en/book/book-title-123456": "BookBeat",
    "https://www.bookbeat.se/bok/titel-123": "BookBeat",

    # Chirp
    "https://www.chirpbooks.com/player/11435746": "Chirp",
    "https://www.chirpbooks.com/audiobooks/title-here": "Chirp",

    # eReolen
    "https://ereolen.dk/ting/object/870970-basis%3A53978223": "Ereolen",
    "https://ereolen.dk/ting/object/some-book-id": "Ereolen",

    # Everand (formerly Scribd)
    "https://www.everand.com/listen/579426746": "Everand",
    "https://www.everand.com/audiobook/123456/Book-Title": "Everand",
    "https://www.scribd.com/listen/579426746": "Everand",  # Legacy Scribd URL
    "https://www.scribd.com/audiobook/123/Title": "Everand",

    # Librivox
    "https://librivox.org/library-of-the-worlds-best-literature-ancient-and-modern-volume-3-by-various/": "Librivox",
    "https://librivox.org/moby-dick-by-herman-melville/": "Librivox",

    # Nextory
    "https://www.nextory.no/bok/somethingsomethingsomething-99999999/": "Nextory",
    "https://www.nextory.se/bok/book-title-123/": "Nextory",
    "https://www.nextory.com/dk/bog/title-456": "Nextory",

    # Overdrive
    "https://ofs-d2b6150a9dec641552f953da2637d146.listen.overdrive.com/?d=...": "Overdrive",
    "https://ofs-abc123.listen.overdrive.com/": "Overdrive",

    # Podimo
    "https://podimo.com/no/shows/show-id": "Podimo",
    "https://podimo.com/dk/shows/another-show": "Podimo",

    # RSS
    "https://example.com/podcast/feed.rss": "RSS",
    "https://feeds.example.com/podcast.xml": "RSS",
    "http://example.com/feed.rss": "RSS",

    # Saxo
    "https://www.saxo.com/dk/audiobooks/title_123456": "Saxo",
    "https://www.saxo.com/no/lydbøker/book-name_789": "Saxo",

    # Storytel
    "https://www.storytel.com/no/nn/books/somethingsomething-9999999": "Storytel",
    "https://www.storytel.com/se/sv/books/book-title-123": "Storytel",
    "https://www.storytel.com/dk/da/books/title-456": "Storytel",
}


class TestURLToSource:
    """Tests for URL to source matching."""

    def test_url_to_source_all_sources(self):
        """Test that all test URLs match to correct source."""
        for url, expected_source_name in TEST_DATA.items():
            source = find_compatible_source(url)
            assert source.__name__ == expected_source_name + "Source", \
                f"URL {url} matched to {source.__name__} instead of {expected_source_name}Source"

    @pytest.mark.parametrize("url,expected", list(TEST_DATA.items()))
    def test_individual_url_matching(self, url, expected):
        """Test individual URL matching (parameterized)."""
        source = find_compatible_source(url)
        assert source.__name__ == expected + "Source"


class TestInvalidURLs:
    """Tests for invalid or unsupported URLs."""

    def test_invalid_url_raises_no_source_found(self):
        """Test that invalid URL raises NoSourceFound."""
        with pytest.raises(NoSourceFound):
            find_compatible_source("https://completely-unknown-site.com/audiobook")

    def test_random_url_no_match(self):
        """Test that random URLs don't match any source."""
        invalid_urls = [
            "https://www.google.com",
            "https://www.github.com",
            "https://www.wikipedia.org",
            "https://example.com",
        ]

        for url in invalid_urls:
            with pytest.raises(NoSourceFound):
                find_compatible_source(url)

    def test_malformed_url(self):
        """Test handling of malformed URLs."""
        with pytest.raises(NoSourceFound):
            find_compatible_source("not-a-valid-url")

    def test_empty_url(self):
        """Test handling of empty URL."""
        with pytest.raises(NoSourceFound):
            find_compatible_source("")


class TestSourceNames:
    """Tests for source name retrieval."""

    def test_get_source_names_returns_list(self):
        """Test that get_source_names returns a list."""
        names = get_source_names()
        assert isinstance(names, list)
        assert len(names) > 0

    def test_get_source_names_includes_expected_sources(self):
        """Test that all expected sources are in the list."""
        names = get_source_names()

        expected_sources = [
            "Audiobooksdotcom",
            "Blinkist",
            "BookBeat",
            "Chirp",
            "Ereolen",
            "Everand",
            "Librivox",
            "Nextory",
            "Overdrive",
            "Podimo",
            "RSS",
            "Saxo",
            "Storytel",
        ]

        # Check that we have at least these sources
        for expected in expected_sources:
            assert any(expected.lower() in name.lower() for name in names), \
                f"Expected source {expected} not found in {names}"

    def test_source_names_are_strings(self):
        """Test that all source names are strings."""
        names = get_source_names()
        assert all(isinstance(name, str) for name in names)


class TestSourceCoverage:
    """Tests for ensuring all sources are covered."""

    def test_all_13_sources_have_test_urls(self):
        """Test that we have test URLs for all 13 sources."""
        # Get all unique source names from test data
        tested_sources = set(TEST_DATA.values())

        # All 13 sources
        expected_sources = {
            "Audiobooksdotcom",
            "Blinkist",
            "BookBeat",
            "Chirp",
            "Ereolen",
            "Everand",
            "Librivox",
            "Nextory",
            "Overdrive",
            "Podimo",
            "RSS",
            "Saxo",
            "Storytel",
        }

        # Check coverage
        assert tested_sources == expected_sources, \
            f"Missing tests for: {expected_sources - tested_sources}"

    def test_minimum_two_urls_per_source(self):
        """Test that we have at least 2 test URLs for most sources."""
        from collections import Counter

        source_counts = Counter(TEST_DATA.values())

        # Most sources should have multiple test URLs
        sources_with_multiple_urls = sum(1 for count in source_counts.values() if count >= 2)
        assert sources_with_multiple_urls >= 10, \
            "Most sources should have multiple test URLs"


class TestURLVariations:
    """Tests for URL variations and edge cases."""

    def test_storytel_different_locales(self):
        """Test Storytel URLs from different locales."""
        storytel_urls = [
            "https://www.storytel.com/no/nn/books/book-123",
            "https://www.storytel.com/se/sv/books/book-456",
            "https://www.storytel.com/dk/da/books/book-789",
        ]

        for url in storytel_urls:
            source = find_compatible_source(url)
            assert source.__name__ == "StorytelSource"

    def test_nextory_different_domains(self):
        """Test Nextory URLs from different domains."""
        nextory_urls = [
            "https://www.nextory.no/bok/title-123/",
            "https://www.nextory.se/bok/title-456/",
            "https://www.nextory.com/dk/bog/title-789",
        ]

        for url in nextory_urls:
            source = find_compatible_source(url)
            assert source.__name__ == "NextorySource"

    def test_everand_and_scribd_compatibility(self):
        """Test that both Everand and Scribd URLs work."""
        everand_url = "https://www.everand.com/listen/123456"
        scribd_url = "https://www.scribd.com/listen/123456"

        source1 = find_compatible_source(everand_url)
        source2 = find_compatible_source(scribd_url)

        # Both should map to Everand
        assert source1.__name__ == "EverandSource"
        assert source2.__name__ == "EverandSource"

    def test_rss_feed_variations(self):
        """Test various RSS feed URL patterns."""
        rss_urls = [
            "https://example.com/feed.rss",
            "https://example.com/podcast.xml",
            "http://feeds.example.com/show.rss",
        ]

        for url in rss_urls:
            source = find_compatible_source(url)
            assert source.__name__ == "RSSSource"


# Legacy test function for backward compatibility
def test_url_to_source():
    """Legacy test function - tests all URLs match correctly."""
    for url, source_name in TEST_DATA.items():
        source = find_compatible_source(url)
        assert source.__name__ == source_name + "Source"
