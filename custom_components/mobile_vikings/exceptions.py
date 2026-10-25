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


class MFAEnabledException(Exception):
    """Raised when MFA is enabled and not supported."""

    pass


class MFARequiredException(Exception):
    """Raised when MFA is required to complete authentication."""

    def __init__(self, mfa_token: str) -> None:
        """Initialize with the MFA token from the API."""
        super().__init__("MFA required")
        self.mfa_token = mfa_token


class NotAuthenticatedException(Exception):
    """Raised when session is invalid."""

    pass


class GatewayTimeoutException(MobileVikingsServiceException):
    """Raised when server times out."""

    pass


class BadGatewayException(MobileVikingsServiceException):
    """Raised when server returns Bad Gateway."""

    pass
