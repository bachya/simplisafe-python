"""Define package errors."""


class SimplipyError(Exception):
    """Define a base error."""


class InvalidCredentialsError(SimplipyError):
    """Define an error related to invalid requests."""


class RequestError(SimplipyError):
    """Define an error related to invalid requests."""
