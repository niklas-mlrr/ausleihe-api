"""Book matching for the inventory Excel commands.

This module deliberately contains no API access and imports no optional Excel
dependency at import time.  The command wrappers own CLI parsing and workbook
loading; this function owns matching validation.

``atomic_save_workbook`` used to live here and moved to
``bestand.core.excel_io`` (repo ``sba-bestand``) on 2026-09-04.  It knows
nothing about IServ or HTTP -- only about the filesystem and openpyxl -- so a
caller that merely wants to save a workbook durably should not have to install
this API client for it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class MatchResult:
    book: Optional[dict[str, Any]]
    error: Optional[str] = None


def match_book(
    books: list[dict[str, Any]], subject: str, hint: Optional[str], *, override_isbn: Optional[str] = None,
    hint_expansions: Optional[dict[str, str]] = None,
) -> MatchResult:
    """Match exactly one book or return an actionable error.

    Selecting the first of several books is unsafe: it can write a real stock
    value into the wrong column.  An override is intentionally ISBN-based so it
    remains stable when a title is edited.
    """
    candidates = [book for book in books if subject in book.get("subjects", [])]
    if override_isbn:
        overridden = [book for book in candidates if book.get("isbn") == override_isbn]
        if len(overridden) == 1:
            return MatchResult(overridden[0])
        return MatchResult(
            None, f"Override ISBN {override_isbn!r} passt nicht eindeutig zu Fach {subject!r}."
        )
    if hint:
        import re

        terms = [hint]
        expansion = (hint_expansions or {}).get(hint.lower())
        if expansion:
            terms.append(expansion)
        def has_hint(book: dict[str, Any]) -> bool:
            title = (book.get("title") or "").lower()
            return any(
                re.search(r"(?<![a-zA-ZäöüÄÖÜß])" + re.escape(term.lower()), title)
                for term in terms
            )

        candidates = [book for book in candidates if has_hint(book)]
    if len(candidates) == 1:
        return MatchResult(candidates[0])
    if not candidates:
        suffix = f" ({hint})" if hint else ""
        return MatchResult(None, f"Kein Buch-Match für Fach {subject!r}{suffix}.")
    isbns = ", ".join(str(book.get("isbn", "?")) for book in candidates)
    return MatchResult(None, f"Mehrdeutiger Buch-Match für Fach {subject!r}: {isbns}. Override erforderlich.")
