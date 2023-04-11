"""A set of custom exceptions."""

__all__ = ["FileExtensionError", "LogDataInvalidError", "ValidationError"]


class ValidationError(Exception):
    """An error indicating that data-object does not comply with the guidelines."""


class FileExtensionError(Exception):
    """An error indicating that the file name has the wrong file extension."""


class LogDataInvalidError(Exception):
    """An error indicating that the log data is invalid."""
