from .client import AusleiheClient
from .exceptions import AusleiheError, AuthError, ForbiddenError, NotFoundError
from .models import Book, BorrowingRule, Series, Student

# Sub-APIs (als Type-Hints / für isinstance nutzbar)
from .admin import AdminAPI
from .books import BookAPI
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
    "NotFoundError",
    "ForbiddenError",
    # Sub-APIs
    "BookAPI",
    "StudentAPI",
    "SeriesAPI",
    "UserAPI",
    "AdminAPI",
    "SchoolyearsAPI",
]
