"""
Tests for exception handling in audiobook-dl.
"""
import pytest
from unittest.mock import Mock, patch

from audiobookdl.exceptions import (
    AudiobookDLException,
    DataNotPresent,
    FailedCombining,
    MissingDependency,
    MissingEncoder,
    NoFilesFound,
    NoSourceFound,
    RequestError,
    UserNotAuthorized,
    CloudflareBlocked,
    MissingBookAccess,
    BookNotFound,
    BookNotReleased,
    BookHasNoAudiobook,
    ConfigNotFound,
    GenericAudiobookDLException,
    DownloadError,
)


class TestAudiobookDLException:
    """Tests for base AudiobookDLException class."""

    def test_base_exception_creation(self):
        """Test creating base exception."""
        exc = AudiobookDLException()
        assert exc.error_description == "unknown"

    def test_exception_with_custom_description(self):
        """Test creating exception with custom description."""
        exc = AudiobookDLException(error_description="custom_error")
        assert exc.error_description == "custom_error"

    def test_exception_with_kwargs(self):
        """Test creating exception with additional data."""
        exc = AudiobookDLException(file="test.mp3", line=42)
        assert exc.data["file"] == "test.mp3"
        assert exc.data["line"] == 42

    @patch("audiobookdl.exceptions.print_error_file")
    def test_exception_print_method(self, mock_print_error):
        """Test exception print method."""
        exc = AudiobookDLException(error_description="test_error", detail="info")
        exc.print()

        mock_print_error.assert_called_once_with("test_error", detail="info")

    def test_exception_is_raisable(self):
        """Test that exception can be raised and caught."""
        with pytest.raises(AudiobookDLException):
            raise AudiobookDLException("test error")


class TestDataNotPresent:
    """Tests for DataNotPresent exception."""

    def test_data_not_present_creation(self):
        """Test creating DataNotPresent exception."""
        exc = DataNotPresent()
        assert exc.error_description == "data_not_present"

    def test_data_not_present_with_element(self):
        """Test DataNotPresent with element information."""
        exc = DataNotPresent(element=".book-title", page="/book/123")
        assert exc.data["element"] == ".book-title"
        assert exc.data["page"] == "/book/123"

    def test_data_not_present_is_catchable(self):
        """Test that DataNotPresent can be caught."""
        with pytest.raises(DataNotPresent) as exc_info:
            raise DataNotPresent(element="missing-field")

        assert exc_info.value.data["element"] == "missing-field"


class TestFailedCombining:
    """Tests for FailedCombining exception."""

    def test_failed_combining_creation(self):
        """Test creating FailedCombining exception."""
        exc = FailedCombining()
        assert exc.error_description == "failed_combining"

    def test_failed_combining_with_details(self):
        """Test FailedCombining with file details."""
        exc = FailedCombining(output="combined.mp3", num_files=10)
        assert exc.data["output"] == "combined.mp3"
        assert exc.data["num_files"] == 10


class TestMissingDependency:
    """Tests for MissingDependency exception."""

    def test_missing_dependency_creation(self):
        """Test creating MissingDependency exception."""
        exc = MissingDependency()
        assert exc.error_description == "missing_dependency"

    def test_missing_dependency_with_name(self):
        """Test MissingDependency with dependency name."""
        exc = MissingDependency(dependency="ffmpeg")
        assert exc.data["dependency"] == "ffmpeg"


class TestMissingEncoder:
    """Tests for MissingEncoder exception."""

    def test_missing_encoder_creation(self):
        """Test creating MissingEncoder exception."""
        exc = MissingEncoder()
        assert exc.error_description == "missing_encoder"

    def test_missing_encoder_with_name(self):
        """Test MissingEncoder with encoder name."""
        exc = MissingEncoder(encoder="libfdk_aac")
        assert exc.data["encoder"] == "libfdk_aac"

    def test_missing_encoder_with_custom_description(self):
        """Test MissingEncoder with custom description."""
        exc = MissingEncoder(
            error_description="FFmpeg encoder 'aac' not found"
        )
        assert "aac" in exc.error_description


class TestNoFilesFound:
    """Tests for NoFilesFound exception."""

    def test_no_files_found_creation(self):
        """Test creating NoFilesFound exception."""
        exc = NoFilesFound()
        assert exc.error_description == "no_files_found"

    def test_no_files_found_with_url(self):
        """Test NoFilesFound with URL information."""
        exc = NoFilesFound(url="https://example.com/book/123")
        assert exc.data["url"] == "https://example.com/book/123"


class TestNoSourceFound:
    """Tests for NoSourceFound exception."""

    def test_no_source_found_creation(self):
        """Test creating NoSourceFound exception."""
        exc = NoSourceFound()
        assert exc.error_description == "no_source_found"

    def test_no_source_found_with_url(self):
        """Test NoSourceFound with URL."""
        exc = NoSourceFound(url="https://unknown-site.com/audiobook")
        assert exc.data["url"] == "https://unknown-site.com/audiobook"

    @patch("audiobookdl.exceptions.sources.get_source_names")
    @patch("audiobookdl.exceptions.print_error_file")
    def test_no_source_found_print_lists_sources(self, mock_print, mock_get_names):
        """Test that NoSourceFound.print() lists available sources."""
        mock_get_names.return_value = ["Storytel", "Nextory", "Librivox"]

        exc = NoSourceFound(url="https://example.com")
        exc.print()

        # Should call print_error_file with source list
        mock_print.assert_called_once()
        call_args = mock_print.call_args
        assert "sources" in call_args[1]
        assert "Storytel" in call_args[1]["sources"]


class TestRequestError:
    """Tests for RequestError exception."""

    def test_request_error_creation(self):
        """Test creating RequestError exception."""
        exc = RequestError()
        assert exc.error_description == "request_error"

    def test_request_error_with_details(self):
        """Test RequestError with request details."""
        exc = RequestError(
            url="https://api.example.com",
            status_code=500,
            message="Internal Server Error"
        )
        assert exc.data["url"] == "https://api.example.com"
        assert exc.data["status_code"] == 500


class TestUserNotAuthorized:
    """Tests for UserNotAuthorized exception."""

    def test_user_not_authorized_creation(self):
        """Test creating UserNotAuthorized exception."""
        exc = UserNotAuthorized()
        assert exc.error_description == "user_not_authorized"

    def test_user_not_authorized_with_message(self):
        """Test UserNotAuthorized with custom message."""
        exc = UserNotAuthorized(error_description="Invalid credentials")
        assert exc.error_description == "Invalid credentials"

    def test_user_not_authorized_with_source(self):
        """Test UserNotAuthorized with source information."""
        exc = UserNotAuthorized(source="Storytel", reason="expired_token")
        assert exc.data["source"] == "Storytel"
        assert exc.data["reason"] == "expired_token"


class TestCloudflareBlocked:
    """Tests for CloudflareBlocked exception."""

    def test_cloudflare_blocked_creation(self):
        """Test creating CloudflareBlocked exception."""
        exc = CloudflareBlocked()
        assert exc.error_description == "cloudflare_blocked"

    def test_cloudflare_blocked_with_url(self):
        """Test CloudflareBlocked with URL."""
        exc = CloudflareBlocked(url="https://protected-site.com")
        assert exc.data["url"] == "https://protected-site.com"


class TestMissingBookAccess:
    """Tests for MissingBookAccess exception."""

    def test_missing_book_access_creation(self):
        """Test creating MissingBookAccess exception."""
        exc = MissingBookAccess()
        assert exc.error_description == "book_access"

    def test_missing_book_access_with_title(self):
        """Test MissingBookAccess with book title."""
        exc = MissingBookAccess(title="The Great Gatsby")
        assert exc.data["title"] == "The Great Gatsby"


class TestBookNotFound:
    """Tests for BookNotFound exception."""

    def test_book_not_found_creation(self):
        """Test creating BookNotFound exception."""
        exc = BookNotFound()
        assert exc.error_description == "book_not_found"

    def test_book_not_found_with_id(self):
        """Test BookNotFound with book ID."""
        exc = BookNotFound(book_id="12345", url="https://example.com/book/12345")
        assert exc.data["book_id"] == "12345"
        assert exc.data["url"] == "https://example.com/book/12345"


class TestBookNotReleased:
    """Tests for BookNotReleased exception."""

    def test_book_not_released_creation(self):
        """Test creating BookNotReleased exception."""
        exc = BookNotReleased()
        assert exc.error_description == "book_not_released"

    def test_book_not_released_with_date(self):
        """Test BookNotReleased with release date."""
        exc = BookNotReleased(title="Upcoming Book", release_date="2025-12-01")
        assert exc.data["title"] == "Upcoming Book"
        assert exc.data["release_date"] == "2025-12-01"


class TestBookHasNoAudiobook:
    """Tests for BookHasNoAudiobook exception."""

    def test_book_has_no_audiobook_creation(self):
        """Test creating BookHasNoAudiobook exception."""
        exc = BookHasNoAudiobook()
        assert exc.error_description == "book_has_no_audiobook"

    def test_book_has_no_audiobook_with_title(self):
        """Test BookHasNoAudiobook with title."""
        exc = BookHasNoAudiobook(title="Text-Only Book")
        assert exc.data["title"] == "Text-Only Book"


class TestConfigNotFound:
    """Tests for ConfigNotFound exception."""

    def test_config_not_found_creation(self):
        """Test creating ConfigNotFound exception."""
        exc = ConfigNotFound()
        assert exc.error_description == "config_not_found"

    def test_config_not_found_with_path(self):
        """Test ConfigNotFound with config path."""
        exc = ConfigNotFound(path="/home/user/.config/audiobook-dl/config.toml")
        assert exc.data["path"] == "/home/user/.config/audiobook-dl/config.toml"


class TestGenericAudiobookDLException:
    """Tests for GenericAudiobookDLException."""

    def test_generic_exception_creation(self):
        """Test creating GenericAudiobookDLException."""
        exc = GenericAudiobookDLException(heading="Error Occurred")
        assert exc.data["heading"] == "Error Occurred"
        assert exc.data["body"] == ""

    def test_generic_exception_with_body(self):
        """Test GenericAudiobookDLException with body text."""
        exc = GenericAudiobookDLException(
            heading="Download Failed",
            body="The server returned an unexpected response."
        )
        assert exc.data["heading"] == "Download Failed"
        assert exc.data["body"] == "The server returned an unexpected response."

    def test_generic_exception_error_description(self):
        """Test GenericAudiobookDLException error description."""
        exc = GenericAudiobookDLException(heading="Test")
        assert exc.error_description == "generic"


class TestDownloadError:
    """Tests for DownloadError exception."""

    def test_download_error_creation(self):
        """Test creating DownloadError exception."""
        exc = DownloadError()
        assert exc.error_description == "download_error"

    def test_download_error_with_status_code(self):
        """Test DownloadError with HTTP status code."""
        exc = DownloadError(
            status_code=403,
            url="https://cdn.example.com/audio.mp3"
        )
        assert exc.data["status_code"] == 403
        assert exc.data["url"] == "https://cdn.example.com/audio.mp3"

    def test_download_error_with_content_type(self):
        """Test DownloadError with unexpected content type."""
        exc = DownloadError(
            content_type="text/html",
            expected_content_type="audio/mpeg",
            expected_status_code=200,
            status_code=200
        )
        assert exc.data["content_type"] == "text/html"
        assert exc.data["expected_content_type"] == "audio/mpeg"


class TestExceptionInheritance:
    """Tests for exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from AudiobookDLException."""
        exceptions = [
            DataNotPresent,
            FailedCombining,
            MissingDependency,
            MissingEncoder,
            NoFilesFound,
            NoSourceFound,
            RequestError,
            UserNotAuthorized,
            CloudflareBlocked,
            MissingBookAccess,
            BookNotFound,
            BookNotReleased,
            BookHasNoAudiobook,
            ConfigNotFound,
            GenericAudiobookDLException,
            DownloadError,
        ]

        for exc_class in exceptions:
            assert issubclass(exc_class, AudiobookDLException)
            assert issubclass(exc_class, Exception)

    def test_exception_can_be_caught_as_base_class(self):
        """Test that specific exceptions can be caught as base class."""
        with pytest.raises(AudiobookDLException):
            raise UserNotAuthorized()

        with pytest.raises(AudiobookDLException):
            raise BookNotFound()

    def test_exception_can_be_caught_specifically(self):
        """Test that exceptions can be caught by specific type."""
        with pytest.raises(DataNotPresent):
            raise DataNotPresent()

        # Should not catch different exception type
        with pytest.raises(UserNotAuthorized):
            try:
                raise UserNotAuthorized()
            except DataNotPresent:
                pytest.fail("Should not catch different exception type")


class TestExceptionUsageScenarios:
    """Tests for realistic exception usage scenarios."""

    def test_catch_and_handle_authentication_error(self):
        """Test catching authentication error in typical flow."""
        def login_user(username, password):
            if username != "valid":
                raise UserNotAuthorized(reason="invalid_username")
            return True

        with pytest.raises(UserNotAuthorized) as exc_info:
            login_user("invalid", "password")

        assert exc_info.value.data["reason"] == "invalid_username"

    def test_catch_and_handle_missing_source(self):
        """Test catching no source found error."""
        def find_source(url):
            if "unknown-site" in url:
                raise NoSourceFound(url=url)
            return "Storytel"

        with pytest.raises(NoSourceFound) as exc_info:
            find_source("https://unknown-site.com/book")

        assert "unknown-site" in exc_info.value.data["url"]

    def test_catch_and_handle_download_error(self):
        """Test catching download error with details."""
        def download_file(url):
            raise DownloadError(
                url=url,
                status_code=403,
                expected_status_code=200
            )

        with pytest.raises(DownloadError) as exc_info:
            download_file("https://cdn.example.com/file.mp3")

        exc = exc_info.value
        assert exc.data["status_code"] == 403
        assert exc.data["expected_status_code"] == 200

    def test_multiple_exceptions_in_try_except(self):
        """Test handling multiple exception types."""
        def risky_operation(scenario):
            if scenario == "auth":
                raise UserNotAuthorized()
            elif scenario == "not_found":
                raise BookNotFound()
            elif scenario == "download":
                raise DownloadError()
            return "success"

        # Test each exception type
        with pytest.raises(UserNotAuthorized):
            risky_operation("auth")

        with pytest.raises(BookNotFound):
            risky_operation("not_found")

        with pytest.raises(DownloadError):
            risky_operation("download")

        # Test success case
        assert risky_operation("success") == "success"

    def test_exception_with_full_context(self):
        """Test exception with comprehensive context information."""
        exc = DownloadError(
            error_description="Failed to download audiobook file",
            url="https://cdn.audiobooks.com/files/123/part1.mp3",
            status_code=403,
            expected_status_code=200,
            content_type="text/html",
            expected_content_type="audio/mpeg",
            attempt=3,
            max_attempts=5
        )

        assert exc.error_description == "Failed to download audiobook file"
        assert exc.data["url"].endswith("part1.mp3")
        assert exc.data["status_code"] == 403
        assert exc.data["attempt"] == 3


class TestExceptionErrorMessages:
    """Tests for exception error message formatting."""

    @patch("audiobookdl.exceptions.print_error_file")
    def test_print_formats_error_correctly(self, mock_print):
        """Test that print method formats errors correctly."""
        exc = DataNotPresent(element=".book-title")
        exc.print()

        mock_print.assert_called_once()
        assert mock_print.call_args[0][0] == "data_not_present"

    @patch("audiobookdl.exceptions.print_error_file")
    def test_print_includes_all_data(self, mock_print):
        """Test that print includes all exception data."""
        exc = DownloadError(
            url="https://example.com",
            status_code=404,
            extra_info="Additional context"
        )
        exc.print()

        call_kwargs = mock_print.call_args[1]
        assert call_kwargs["url"] == "https://example.com"
        assert call_kwargs["status_code"] == 404
        assert call_kwargs["extra_info"] == "Additional context"
