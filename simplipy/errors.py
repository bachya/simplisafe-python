"""Define package errors."""


class SimplipyError(Exception):
    """Define a base error."""
    pass


class RequestError(SimplipyError):
    """Define an error related to invalid requests."""
    pass


class TokenExpiredError(SimplipyError):
    """Define an error for expired access tokens."""
    pass
