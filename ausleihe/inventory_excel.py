"""Safe, testable primitives shared by the inventory Excel commands.

This module deliberately contains no API access and imports no optional Excel
dependency at import time.  The command wrappers own CLI parsing and workbook
loading; these functions own matching validation and durable output.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
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


def atomic_save_workbook(
    workbook: Any, destination: Path, *, backup_dir: Optional[Path] = None
) -> Optional[Path]:
    """Durably replace a workbook and retain a timestamped recovery copy.

    The temporary file is placed next to the source so ``os.replace`` is atomic
    on normal local filesystems.  The original is never touched until the new
    workbook has been completely written.
    """
    destination = destination.resolve()
    if not destination.exists():
        raise FileNotFoundError(f"Excel-Datei nicht gefunden: {destination}")
    backup: Optional[Path] = None
    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = backup_dir / f"{destination.stem}.{stamp}{destination.suffix}"
        # Avoid silently overwriting two saves within the same second.
        counter = 1
        while backup.exists():
            backup = backup_dir / f"{destination.stem}.{stamp}-{counter}{destination.suffix}"
            counter += 1
        shutil.copy2(destination, backup)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{destination.stem}.", suffix=destination.suffix, dir=destination.parent
    )
    try:
        os.close(fd)
        workbook.save(tmp_name)
        with open(tmp_name, "rb") as handle:
            os.fsync(handle.fileno())
        shutil.copymode(destination, tmp_name)
        os.replace(tmp_name, destination)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise
    return backup
