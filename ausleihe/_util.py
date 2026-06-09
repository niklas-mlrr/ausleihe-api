from __future__ import annotations

from urllib.parse import quote


def encode_schoolyear(schoolyear_id: str) -> str:
    """Schuljahr-IDs sind Strings wie '2025/2026' und müssen für die URL
    vollständig encodet werden ('2025%2F2026')."""
    return quote(schoolyear_id, safe="")
