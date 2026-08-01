from __future__ import annotations

from typing import TYPE_CHECKING

from ._util import encode_path_segment, name_params
from .models import Book, Student

if TYPE_CHECKING:
    from .client import AusleiheClient


class StudentAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(
        self,
        include_deleted: bool = False,
        include_anonymized: bool = True,
    ) -> list[Student]:
        params: dict[str, str] = {}
        if include_deleted:
            params["deleted"] = "true"
        # ``anonymized=false`` blendet anonymisierte (DSGVO) Datensätze aus; nur in
        # Kombination mit deleted=true sinnvoll (727 aktiv → 1798 mit deleted →
        # 1497 ohne anonymisierte). Verifiziert 2026-06-10.
        if not include_anonymized:
            params["anonymized"] = "false"
        raw = self._client.get("/students", params=params)
        return [Student.from_dict(d) for d in raw]

    def get_by_id(self, student_id: int) -> Student:
        raw = self._client.get(f"/students/{encode_path_segment(student_id)}")
        return Student.from_dict(raw)

    def get_detail(
        self,
        student_id: int,
        *,
        forms: bool = False,
        enrollments: bool = False,
        books: bool = False,
        claims: bool = False,
    ) -> dict:
        """Schüler-Datensatz mit optional eingebetteten Beziehungen (rohes dict).

        Über Expansion-Query-Parameter (``GET /students/:id?forms=true&…``) liefert
        der Server dieselbe Verschachtelung wie ``/me`` für einen beliebigen Schüler
        — in **einem** Request statt mehrerer. Verifiziert 2026-06-10:

        - ``forms=True`` → ``forms[]`` (Klassenzugehörigkeit nach Jahr)
        - ``enrollments=True`` → ``enrollments[]`` **und** ``participations[]``
        - ``books=True`` → ``books[]`` (aktuell ausgeliehen)
        - ``claims=True`` → ``claims[]`` (erfordert Helfer+/Admin)

        Gibt das rohe dict zurück (die ``Student``-Dataclass hält die Beziehungen
        nicht). Ohne Flags entspricht das Ergebnis ``get_by_id`` als dict.
        """
        params: dict[str, str] = {}
        if forms:
            params["forms"] = "true"
        if enrollments:
            params["enrollments"] = "true"
        if books:
            params["books"] = "true"
        if claims:
            params["claims"] = "true"
        return self._client.get(f"/students/{encode_path_segment(student_id)}", params=params)

    def get_books(self, student_id: int) -> list[Book]:
        raw = self._client.get(f"/students/{encode_path_segment(student_id)}/books")
        return [Book.from_dict(d) for d in raw]

    def get_claims(self, student_id: int) -> list[dict]:
        """Forderungen eines Schülers. Erfordert mod_sbl_grant_always_enrollments oder Admin."""
        return self._client.get(f"/students/{encode_path_segment(student_id)}/claims")

    def get_me(self) -> dict:
        """Eigenes Schüler-Profil inkl. books[], forms[], claims[], enrollments[]."""
        return self._client.get("/me")

    def search_by_name(self, lastname: str = "", firstname: str = "") -> list[Student]:
        if not lastname and not firstname:
            return self.get_all()
        raw = self._client.get("/students/", params=name_params(lastname, firstname))
        return [Student.from_dict(d) for d in raw]
