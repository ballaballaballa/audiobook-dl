import audiobookdl.sources as sources
from .logging import print_error_file, error
from typing import Optional
from rich.markup import escape

class AudiobookDLException(Exception):
    error_description = "unknown"

    def __init__(self, error_description = None, message: Optional[str] = None, **kwargs) -> None:
        if error_description:
            self.error_description = error_description
        self.message = message
        self.data = kwargs
        super().__init__(message or self.error_description)

    def print(self) -> None:
        print_error_file(self.error_description, **self.data)
        if self.message:
            error(escape(self.message))

class DataNotPresent(AudiobookDLException):
    error_description = "data_not_present"

class FailedCombining(AudiobookDLException):
    error_description = "failed_combining"

class MissingDependency(AudiobookDLException):
    error_description = "missing_dependency"

class MissingEncoder(AudiobookDLException):
    error_description = "missing_encoder"

class NoFilesFound(AudiobookDLException):
    error_description = "no_files_found"

class NoSourceFound(AudiobookDLException):
    error_description = "no_source_found"

    def print(self):
        source_name_list = "\n".join([f" • {name}" for name in sources.get_source_names()])
        print_error_file(self.error_description, sources=source_name_list, **self.data)

class RequestError(AudiobookDLException):
    error_description = "request_error"

class UserNotAuthorized(AudiobookDLException):
    error_description = "user_not_authorized"

class CloudflareBlocked(AudiobookDLException):
    error_description = "cloudflare_blocked"

class MissingBookAccess(AudiobookDLException):
    error_description = "book_access"

class BookNotFound(AudiobookDLException):
    error_description = "book_not_found"

class BookNotReleased(AudiobookDLException):
    error_description = "book_not_released"

class BookHasNoAudiobook(AudiobookDLException):
    error_description = "book_has_no_audiobook"

class ConfigNotFound(AudiobookDLException):
    error_description = "config_not_found"

class GenericAudiobookDLException(AudiobookDLException):
    error_description: str = "generic"

    def __init__(self, heading: str, body: Optional[str] = None) -> None:
        self.data = {'heading': heading, 'body': body if body else ""}

class DownloadError(AudiobookDLException):
    error_description: str = "download_error"