"""Exceptions used by MobileVikings."""


class MobileVikingsException(Exception):
    """Base class for all exceptions raised by MobileVikings."""

    pass


class MobileVikingsServiceException(Exception):
    """Raised when service is not available."""

    pass


class BadCredentialsException(Exception):
    """Raised when credentials are incorrect."""

    pass


class NotAuthenticatedException(Exception):
    """Raised when session is invalid."""

    pass


class GatewayTimeoutException(MobileVikingsServiceException):
    """Raised when server times out."""

    pass


class BadGatewayException(MobileVikingsServiceException):
    """Raised when server returns Bad Gateway."""

    pass
