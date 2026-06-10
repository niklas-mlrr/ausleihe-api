from __future__ import annotations

from urllib.parse import quote


def encode_schoolyear(schoolyear_id: str) -> str:
    """Schuljahr-IDs sind Strings wie '2025/2026' und müssen für die URL
    vollständig encodet werden ('2025%2F2026')."""
    return quote(schoolyear_id, safe="")


def name_params(lastname: str = "", firstname: str = "") -> dict[str, str]:
    """Query-Parameter für die Typeahead-Namenssuche (Schüler + IServ-Nutzer)."""
    params: dict[str, str] = {}
    if lastname:
        params["lastname"] = lastname
    if firstname:
        params["firstname"] = firstname
    return params
