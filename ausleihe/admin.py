from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .models import Book

if TYPE_CHECKING:
    from .client import AusleiheClient


class AdminAPI:
    """Endpunkte, die mod_sbl_role_manager (Verwalter) erfordern."""

    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Schuljahre
    # ------------------------------------------------------------------

    def get_schoolyears(self) -> list[dict]:
        return self._client.get("/schoolyears")

    def get_booklists(self, schoolyear_id: int) -> list[dict]:
        return self._client.get(f"/schoolyears/{schoolyear_id}/booklists/")

    def get_booklist_pdf(self, schoolyear_id: int, booklist_id: int) -> bytes:
        self._client._ensure_token()
        resp = self._client._session.get(
            f"{self._client._api_base}schoolyears/{schoolyear_id}/booklists/{booklist_id}/pdf",
            params={"token": self._client._jwt},
        )
        resp.raise_for_status()
        return resp.content

    # ------------------------------------------------------------------
    # Anmeldungen
    # ------------------------------------------------------------------

    def get_enrollments(self, schoolyear_id: int) -> list[dict]:
        return self._client.get(f"/schoolyears/{schoolyear_id}/enrollments/")

    def get_enrollments_export_pdf(self, schoolyear_id: int) -> bytes:
        self._client._ensure_token()
        resp = self._client._session.get(
            f"{self._client._api_base}schoolyears/{schoolyear_id}/enrollments/export/exemptions-remissions",
            params={"token": self._client._jwt},
        )
        resp.raise_for_status()
        return resp.content

    def get_form_students_pdf(self, schoolyear_id: int) -> bytes:
        self._client._ensure_token()
        resp = self._client._session.get(
            f"{self._client._api_base}schoolyears/{schoolyear_id}/forms/export/form-students",
            params={"token": self._client._jwt},
        )
        resp.raise_for_status()
        return resp.content

    # ------------------------------------------------------------------
    # Systemeinstellungen
    # ------------------------------------------------------------------

    def get_settings(self) -> dict:
        return self._client.get("/settings")

    # ------------------------------------------------------------------
    # Forderungen
    # ------------------------------------------------------------------

    def get_claims(self) -> list[dict]:
        return self._client.get("/claims")

    def get_claim_letters_pdf(self, **params: Any) -> bytes:
        """PDF mit Mahnbriefen. Zusätzliche Query-Parameter per kwargs übergeben."""
        self._client._ensure_token()
        resp = self._client._session.get(
            f"{self._client._api_base}claim_letters/pdf/",
            params={"token": self._client._jwt, **params},
        )
        resp.raise_for_status()
        return resp.content

    # ------------------------------------------------------------------
    # Schüler-ID-Barcodes
    # ------------------------------------------------------------------

    def get_student_id(self, code: str) -> dict:
        return self._client.get(f"/studentids/{code}")

    def set_student_id(self, code: str, student_id: int) -> dict:
        return self._client.post(f"/studentids/{code}", json={"student": student_id})

    # ------------------------------------------------------------------
    # Finanzen
    # ------------------------------------------------------------------

    def get_bank(self) -> dict:
        return self._client.get("/bank")

    def get_transactions(self, format: Optional[str] = None) -> list[dict]:
        params = {"format": format} if format else {}
        return self._client.get("/transactions/", params=params)

    # ------------------------------------------------------------------
    # Serien-Exemplare
    # ------------------------------------------------------------------

    def get_series_books(self, isbn: str) -> list[Book]:
        raw = self._client.get(f"/series/{isbn}/books")
        return [Book.from_dict(d) for d in raw]
