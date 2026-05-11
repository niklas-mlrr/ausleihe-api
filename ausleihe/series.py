from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Series

if TYPE_CHECKING:
    from .client import AusleiheClient


class SeriesAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self) -> list[Series]:
        raw = self._client.get("/series")
        return [Series.from_dict(d) for d in raw]

    def get_by_isbn(self, isbn: str) -> Series:
        raw = self._client.get(f"/series/{isbn}")
        return Series.from_dict(raw)

    def get_publishers(self) -> list[str]:
        raw = self._client.get("/series/publishers")
        return [d["publisher"] for d in raw if "publisher" in d]

    def get_subjects(self) -> list[str]:
        raw = self._client.get("/series/subjects")
        return [d["subject"] for d in raw if "subject" in d]

    def get_grades(self) -> list[dict]:
        return self._client.get("/series/grades")
