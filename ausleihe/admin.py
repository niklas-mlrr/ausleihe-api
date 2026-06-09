from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ._util import encode_schoolyear
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

    def get_booklists(self, schoolyear_id: str) -> list[dict]:
        # Identischer GET-Endpunkt wie client.schoolyears.get_booklists — dort liegt
        # die Implementierung, hier nur als Convenience im Admin-Namespace.
        return self._client.schoolyears.get_booklists(schoolyear_id)

    def get_booklist_pdf(self, schoolyear_id: str, booklist_id: int) -> bytes:
        sy = encode_schoolyear(schoolyear_id)
        return self._client._get_binary(f"schoolyears/{sy}/booklists/{booklist_id}/pdf")

    # ------------------------------------------------------------------
    # Anmeldungen
    # ------------------------------------------------------------------

    def get_enrollments(self, schoolyear_id: str) -> list[dict]:
        return self._client.get(f"/schoolyears/{encode_schoolyear(schoolyear_id)}/enrollments/")

    def get_enrollments_export_pdf(self, schoolyear_id: str) -> bytes:
        sy = encode_schoolyear(schoolyear_id)
        return self._client._get_binary(f"schoolyears/{sy}/enrollments/export/exemptions-remissions")

    def get_form_students_pdf(self, schoolyear_id: str) -> bytes:
        sy = encode_schoolyear(schoolyear_id)
        return self._client._get_binary(f"schoolyears/{sy}/forms/export/form-students")

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
        return self._client._get_binary("claim_letters/pdf/", **params)

    # ------------------------------------------------------------------
    # Schüler-ID-Barcodes
    # ------------------------------------------------------------------

    def get_student_id(self, code: str) -> dict:
        return self._client.get(f"/studentids/{code}")

    def set_student_id(self, code: str, student_id: int) -> dict:
        # SCHREIBEND — wirkt auf die Produktion. Nur mit AusleiheClient(allow_writes=True).
        # Das Frontend nutzt hierfür PUT /studentids/:code (aus dem $resource-Bundle).
        return self._client.put(f"/studentids/{code}", json={"student": student_id})

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
