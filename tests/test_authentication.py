"""
Tests for authentication functionality in audiobook-dl.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from http.cookiejar import MozillaCookieJar, Cookie
import requests

from audiobookdl.sources.source import Source
from audiobookdl.exceptions import UserNotAuthorized


class TestSource(Source):
    """Test implementation of Source class."""
    names = ["TestSource"]
    match = [r"https://test\.example\.com/.*"]
    _authentication_methods = ["cookies", "login"]
    login_data = ["username", "password"]

    def _login(self, url: str, username: str, password: str):
        """Mock login implementation."""
        if username == "valid@example.com" and password == "validpassword":
            # Simulate successful login by adding session cookie
            self._session.cookies.set("session_id", "valid_session_token")
        else:
            raise UserNotAuthorized("Invalid credentials")

    def download(self, url: str):
        """Mock download implementation."""
        pass


@pytest.fixture
def mock_options():
    """Provide mock options object."""
    options = Mock()
    options.database_directory = "/tmp/audiobook-dl"
    options.skip_downloaded = False
    return options


@pytest.fixture
def test_source(mock_options):
    """Provide a test source instance."""
    return TestSource(mock_options)


class TestSourceAuthentication:
    """Tests for Source authentication methods."""

    def test_source_requires_authentication(self, test_source):
        """Test that source correctly reports if authentication is required."""
        assert test_source.requires_authentication is True
        assert len(test_source._authentication_methods) > 0

    def test_source_not_authenticated_initially(self, test_source):
        """Test that source is not authenticated on creation."""
        assert test_source.authenticated is False

    def test_source_supports_cookies(self, test_source):
        """Test that source correctly reports cookie support."""
        assert test_source.supports_cookies is True
        assert "cookies" in test_source._authentication_methods

    def test_source_supports_login(self, test_source):
        """Test that source correctly reports login support."""
        assert test_source.supports_login is True
        assert "login" in test_source._authentication_methods


class TestCookieAuthentication:
    """Tests for cookie-based authentication."""

    def test_load_cookie_file(self, test_source, sample_cookies_txt):
        """Test loading cookies from a Netscape cookie file."""
        test_source.load_cookie_file(str(sample_cookies_txt))

        # Check that cookies were loaded
        assert test_source.authenticated is True
        assert len(test_source._session.cookies) > 0

    def test_load_cookie_file_sets_authenticated(self, test_source, sample_cookies_txt):
        """Test that loading cookies sets authenticated flag."""
        assert test_source.authenticated is False
        test_source.load_cookie_file(str(sample_cookies_txt))
        assert test_source.authenticated is True

    def test_load_cookie_file_invalid_path(self, test_source):
        """Test handling of invalid cookie file path."""
        with pytest.raises(FileNotFoundError):
            test_source.load_cookie_file("/nonexistent/cookies.txt")

    @pytest.mark.unit
    def test_cookies_added_to_session(self, test_source, sample_cookies_txt):
        """Test that cookies are actually added to the session."""
        test_source.load_cookie_file(str(sample_cookies_txt))

        # Check specific cookies
        cookies_dict = dict(test_source._session.cookies)
        assert "session_id" in cookies_dict
        assert "auth_token" in cookies_dict
        assert cookies_dict["session_id"] == "abc123"
        assert cookies_dict["auth_token"] == "def456"

    def test_cookie_file_with_comments(self, temp_dir, test_source):
        """Test that cookie file with comments is parsed correctly."""
        cookies_file = temp_dir / "cookies_with_comments.txt"
        cookies_content = """# Netscape HTTP Cookie File
# This is a comment
# Another comment

.example.com\tTRUE\t/\tFALSE\t1234567890\ttest_cookie\ttest_value
"""
        cookies_file.write_text(cookies_content)

        test_source.load_cookie_file(str(cookies_file))
        assert test_source.authenticated is True
        assert test_source._session.cookies.get("test_cookie") == "test_value"


class TestLoginAuthentication:
    """Tests for username/password login authentication."""

    def test_login_with_valid_credentials(self, test_source):
        """Test login with valid username and password."""
        test_source.login(
            url="https://test.example.com/login",
            username="valid@example.com",
            password="validpassword",
        )

        assert test_source.authenticated is True
        # Check that session cookie was set
        assert test_source._session.cookies.get("session_id") == "valid_session_token"

    def test_login_with_invalid_credentials(self, test_source):
        """Test login with invalid credentials raises exception."""
        with pytest.raises(UserNotAuthorized):
            test_source.login(
                url="https://test.example.com/login",
                username="invalid@example.com",
                password="wrongpassword",
            )

        # Should not be authenticated after failed login
        assert test_source.authenticated is False

    def test_login_sets_authenticated_flag(self, test_source):
        """Test that successful login sets authenticated flag."""
        assert test_source.authenticated is False

        test_source.login(
            url="https://test.example.com/login",
            username="valid@example.com",
            password="validpassword",
        )

        assert test_source.authenticated is True

    @pytest.mark.unit
    def test_login_with_missing_username(self, test_source):
        """Test login with missing username."""
        with pytest.raises(TypeError):
            test_source.login(
                url="https://test.example.com/login",
                password="validpassword",
            )

    @pytest.mark.unit
    def test_login_with_missing_password(self, test_source):
        """Test login with missing password."""
        with pytest.raises(TypeError):
            test_source.login(
                url="https://test.example.com/login",
                username="valid@example.com",
            )


class TestSourceWithoutAuthentication:
    """Tests for sources that don't require authentication."""

    def test_source_without_auth_methods(self, mock_options):
        """Test source that doesn't require authentication."""

        class NoAuthSource(Source):
            names = ["NoAuthSource"]
            match = [r"https://noauth\.example\.com/.*"]
            _authentication_methods = []

            def download(self, url: str):
                pass

        source = NoAuthSource(mock_options)
        assert source.requires_authentication is False
        assert source.authenticated is False
        assert source.supports_cookies is False
        assert source.supports_login is False


class TestCookieOnlySource:
    """Tests for sources that only support cookie authentication."""

    def test_cookie_only_source(self, mock_options, sample_cookies_txt):
        """Test source that only supports cookies."""

        class CookieOnlySource(Source):
            names = ["CookieOnlySource"]
            match = [r"https://cookieonly\.example\.com/.*"]
            _authentication_methods = ["cookies"]

            def download(self, url: str):
                pass

        source = CookieOnlySource(mock_options)
        assert source.requires_authentication is True
        assert source.supports_cookies is True
        assert source.supports_login is False

        # Test cookie loading works
        source.load_cookie_file(str(sample_cookies_txt))
        assert source.authenticated is True


class TestLoginOnlySource:
    """Tests for sources that only support login authentication."""

    def test_login_only_source(self, mock_options):
        """Test source that only supports username/password login."""

        class LoginOnlySource(Source):
            names = ["LoginOnlySource"]
            match = [r"https://loginonly\.example\.com/.*"]
            _authentication_methods = ["login"]
            login_data = ["username", "password"]

            def _login(self, url: str, username: str, password: str):
                if username == "test@example.com":
                    self._session.cookies.set("auth", "token123")
                else:
                    raise UserNotAuthorized("Login failed")

            def download(self, url: str):
                pass

        source = LoginOnlySource(mock_options)
        assert source.requires_authentication is True
        assert source.supports_cookies is False
        assert source.supports_login is True

        # Test login works
        source.login(
            url="https://loginonly.example.com/login",
            username="test@example.com",
            password="testpass",
        )
        assert source.authenticated is True


class TestAuthenticationPersistence:
    """Tests for authentication state persistence across requests."""

    def test_cookies_persist_across_requests(self, test_source, sample_cookies_txt):
        """Test that cookies persist in session across multiple requests."""
        test_source.load_cookie_file(str(sample_cookies_txt))

        # Simulate multiple requests
        initial_cookies = dict(test_source._session.cookies)

        # Add additional cookie (simulating server response)
        test_source._session.cookies.set("new_cookie", "new_value")

        # Check all cookies are still present
        updated_cookies = dict(test_source._session.cookies)
        assert "session_id" in updated_cookies
        assert "auth_token" in updated_cookies
        assert "new_cookie" in updated_cookies

    def test_authentication_state_maintained(self, test_source):
        """Test that authentication state is maintained."""
        # Login
        test_source.login(
            url="https://test.example.com/login",
            username="valid@example.com",
            password="validpassword",
        )

        # State should remain authenticated
        assert test_source.authenticated is True

        # Simulate multiple operations
        for _ in range(5):
            _ = test_source.authenticated
            assert test_source.authenticated is True


class TestAuthenticationEdgeCases:
    """Tests for edge cases in authentication."""

    def test_empty_cookie_file(self, temp_dir, test_source):
        """Test handling of empty cookie file."""
        empty_cookies = temp_dir / "empty.txt"
        empty_cookies.write_text("# Netscape HTTP Cookie File\n")

        test_source.load_cookie_file(str(empty_cookies))
        # Should be marked as authenticated even with empty file
        assert test_source.authenticated is True

    def test_malformed_cookie_file(self, temp_dir, test_source):
        """Test handling of malformed cookie file."""
        malformed_cookies = temp_dir / "malformed.txt"
        malformed_cookies.write_text("This is not a valid cookie file")

        with pytest.raises(Exception):  # cookiejar raises various exceptions
            test_source.load_cookie_file(str(malformed_cookies))

    def test_login_empty_credentials(self, test_source):
        """Test login with empty credentials."""
        with pytest.raises(UserNotAuthorized):
            test_source.login(
                url="https://test.example.com/login",
                username="",
                password="",
            )

    def test_multiple_authentication_methods(self, test_source, sample_cookies_txt):
        """Test using both cookies and login (cookies first)."""
        # First authenticate with cookies
        test_source.load_cookie_file(str(sample_cookies_txt))
        assert test_source.authenticated is True

        # Then login (should work and maintain authenticated state)
        test_source.login(
            url="https://test.example.com/login",
            username="valid@example.com",
            password="validpassword",
        )
        assert test_source.authenticated is True
