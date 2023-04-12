"""A set of custom exceptions."""

__all__ = ["FileExtensionError", "LogDataParseError", "ValidationError"]


class ValidationError(Exception):
    """An error indicating that data-object does not comply with the guidelines."""


class FileExtensionError(Exception):
    """An error indicating that the file name has the wrong file extension."""


class LogDataParseError(Exception):
    """An error indicating issues while parsing log data."""
