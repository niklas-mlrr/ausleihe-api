from __future__ import annotations

from typing import TYPE_CHECKING

from ._util import encode_path_segment
from .models import Series

if TYPE_CHECKING:
    from .client import AusleiheClient


class SeriesAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self, detailed: bool = False) -> list[Series]:
        """Alle Buchserien (Titel-Ebene).

        Mit ``detailed=True`` (``GET /series?detailed=true``) liefert der Server
        zusätzlich ``total`` (Exemplare gesamt) und ``available`` (verfügbar) je
        Serie — andernfalls sind diese nur über ``get_by_isbn`` pro Serie verfügbar.
        Spart 296 Einzelabfragen, wenn man die Bestände aller Serien braucht.
        """
        params = {"detailed": "true"} if detailed else {}
        raw = self._client.get("/series", params=params)
        return [Series.from_dict(d) for d in raw]

    def get_by_isbn(self, isbn: str) -> Series:
        raw = self._client.get(f"/series/{encode_path_segment(isbn)}")
        return Series.from_dict(raw)

    def get_publishers(self) -> list[str]:
        raw = self._client.get("/series/publishers")
        return [d["publisher"] for d in raw if "publisher" in d]

    def get_subjects(self) -> list[str]:
        raw = self._client.get("/series/subjects")
        return [d["subject"] for d in raw if "subject" in d]

    def get_grades(self) -> list[dict]:
        return self._client.get("/series/grades")
