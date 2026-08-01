# Sub-APIs (als Type-Hints / für isinstance nutzbar)
from .admin import AdminAPI
from .books import BookAPI
from .client import AusleiheClient
from .exceptions import (
    AusleiheError,
    AuthError,
    ConfigurationError,
    ForbiddenError,
    NotFoundError,
    TransportError,
)
from .models import Book, BorrowingRule, Series, Student
from .schoolyears import SchoolyearsAPI
from .series import SeriesAPI
from .students import StudentAPI
from .users import UserAPI

__all__ = [
    "AusleiheClient",
    # Modelle
    "Book",
    "Student",
    "Series",
    "BorrowingRule",
    # Exceptions
    "AusleiheError",
    "AuthError",
    "ConfigurationError",
    "NotFoundError",
    "ForbiddenError",
    "TransportError",
    # Sub-APIs
    "BookAPI",
    "StudentAPI",
    "SeriesAPI",
    "UserAPI",
    "AdminAPI",
    "SchoolyearsAPI",
]
