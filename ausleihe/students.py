from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Book, Student

if TYPE_CHECKING:
    from .client import AusleiheClient


class StudentAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self, include_deleted: bool = False) -> list[Student]:
        params = {"deleted": "true"} if include_deleted else {}
        raw = self._client.get("/students", params=params)
        return [Student.from_dict(d) for d in raw]

    def get_by_id(self, student_id: int) -> Student:
        raw = self._client.get(f"/students/{student_id}")
        return Student.from_dict(raw)

    def get_books(self, student_id: int) -> list[Book]:
        raw = self._client.get(f"/students/{student_id}/books")
        return [Book.from_dict(d) for d in raw]

    def get_claims(self, student_id: int) -> list[dict]:
        """Forderungen eines Schülers. Erfordert mod_sbl_grant_always_enrollments oder Admin."""
        return self._client.get(f"/students/{student_id}/claims")

    def search_by_name(self, lastname: str = "", firstname: str = "") -> list[Student]:
        if not lastname and not firstname:
            return self.get_all()
        params: dict = {}
        if lastname:
            params["lastname"] = lastname
        if firstname:
            params["firstname"] = firstname
        raw = self._client.get("/students/", params=params)
        return [Student.from_dict(d) for d in raw]
