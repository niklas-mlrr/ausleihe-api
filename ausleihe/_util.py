from __future__ import annotations

from urllib.parse import quote


def encode_path_segment(value: object) -> str:
    """Encode one dynamic URL path segment, never an entire path."""
    return quote(str(value), safe="")


def encode_schoolyear(schoolyear_id: str) -> str:
    """Schuljahr-IDs sind Strings wie '2025/2026' und müssen für die URL
    vollständig encodet werden ('2025%2F2026')."""
    return encode_path_segment(schoolyear_id)


def name_params(lastname: str = "", firstname: str = "") -> dict[str, str]:
    """Query-Parameter für die Typeahead-Namenssuche (Schüler + IServ-Nutzer)."""
    params: dict[str, str] = {}
    if lastname:
        params["lastname"] = lastname
    if firstname:
        params["firstname"] = firstname
    return params
