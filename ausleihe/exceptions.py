from __future__ import annotations


class AusleiheError(Exception):
    pass


class AuthError(AusleiheError):
    pass


class NotFoundError(AusleiheError):
    pass


class ForbiddenError(AusleiheError):
    pass
