from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from .client import AusleiheClient


class SchoolyearsAPI:
    """Schuljahres- und Bücherlisten-Endpunkte. Helfer-zugänglich."""

    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    @staticmethod
    def _enc(schoolyear_id: str) -> str:
        return quote(schoolyear_id, safe="")

    def get_current(self) -> dict:
        """Aktuelles Schuljahr. ID ist String wie '2025/2026'."""
        return self._client.get("/schoolyears/current")

    def get_by_id(self, schoolyear_id: str) -> dict:
        """Einzelnes Schuljahr mit Booklists[]. ID z.B. '2025/2026'."""
        return self._client.get(f"/schoolyears/{self._enc(schoolyear_id)}")

    def get_booklists(self, schoolyear_id: str) -> list[dict]:
        """Alle Bücherlisten eines Schuljahrs. ID z.B. '2025/2026'."""
        return self._client.get(f"/schoolyears/{self._enc(schoolyear_id)}/booklists/")

    def get_booklist(self, schoolyear_id: str, booklist_id: int) -> dict:
        """Einzelne Bücherliste mit sections[]->options[]->items[]. ID z.B. '2025/2026'."""
        return self._client.get(
            f"/schoolyears/{self._enc(schoolyear_id)}/booklists/{booklist_id}"
        )
