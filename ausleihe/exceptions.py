from __future__ import annotations


class AusleiheError(Exception):
    """Base class for errors raised by this client."""


class ConfigurationError(AusleiheError):
    """Local client configuration is incomplete or unsafe."""


class TransportError(AusleiheError):
    """The server could not be reached or did not return a usable response."""


class AuthError(AusleiheError):
    pass


class NotFoundError(AusleiheError):
    pass


class ForbiddenError(AusleiheError):
    pass
