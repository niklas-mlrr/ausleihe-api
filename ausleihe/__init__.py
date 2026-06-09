from .client import AusleiheClient
from .exceptions import AusleiheError, AuthError, ForbiddenError, NotFoundError
from .models import Book, BorrowingRule, Series, Student

__all__ = [
    "AusleiheClient",
    "Book",
    "Student",
    "Series",
    "BorrowingRule",
    "AusleiheError",
    "AuthError",
    "NotFoundError",
    "ForbiddenError",
    # Sub-APIs (als Type-Hints nutzbar)
    "AdminAPI",
    "SchoolyearsAPI",
]

from .admin import AdminAPI  # noqa: E402
from .schoolyears import SchoolyearsAPI  # noqa: E402
