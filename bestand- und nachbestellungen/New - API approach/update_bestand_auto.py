#!/usr/bin/env python3
"""Auto-Discovery: befüllt 'Angemeldet'- und 'Bezahlt'-Zellen automatisch.

Im Unterschied zu update_bestand.py braucht dieses Skript keine config.json-Mappings.
Es liest die Excel-Struktur selbst aus und matched Bücher anhand von Fach-Zeilen.

Algorithmus:
  - Spalte A zeilenweise von oben durchgehen
  - "Fach"-Zeile oder "Zustand"-Zeile → merken
  - "Jahrgang X"-Zeile → ausleihbare Bücher für diesen Jahrgang laden (API GET)
      - Gefiltert: borrowable=True, Leihpreis > 0, kein "eBook" im Titel
  - Für jede Spalte: Fach-Label aus nächster darüber liegender Fach-Zeile bestimmen
      - Klammerzusatz im Fach (z.B. "Politik (eA)") = Hinweis auf Serientitel, nicht Teil des Fachs
      - Falls Fach-Zelle leer → nächst höhere Fach-Zeile als Fallback
  - Zustand-Label aus nächster darüber liegender Zustand-Zeile bestimmen
      - Falls leer → Fallback auf nächst höhere Zustand-Zeile
  - Passt das Buch und ist Zustand "Angemeldet" oder "Bezahlt" → Wert eintragen
  - Bereits bearbeitete Ankerzellen überspringen (Mehrjahresbände / Zellenverbünde)
  - Abbruch nach mehr als 3 nicht identifizierbaren Zeilen in Folge

Verwendung:
    python3 update_bestand_auto.py [--dry-run] [--schoolyear 2025/2026]
                                   [--excel "Bestand- und Nachbestellungsliste 2026.xlsx"]
                                   [--sheet "Bestand- und Nachbestellung"]

Nur GET-Zugriffe auf die API. Kein Schreiben in die Datenbank.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from ausleihe import AusleiheClient, NotFoundError


# ── Excel-Hilfsfunktionen ─────────────────────────────────────────────────────

def resolve_anchor(ws, row: int, col: int) -> tuple[int, int]:
    """Gibt (anchor_row, anchor_col) zurück – bei Zellenverbund die oben-links-Zelle."""
    cell_ref = f"{get_column_letter(col)}{row}"
    for merged in ws.merged_cells.ranges:
        if cell_ref in merged:
            return merged.min_row, merged.min_col
    return row, col


def find_fach_for_col(ws, fach_rows: list[int], col: int) -> str | None:
    """Fach-Label für Spalte col aus der nächsten (untersten) Fach-Zeile mit Inhalt.
    Ist die Zelle leer, wird die nächsthöhere Fach-Zeile als Fallback genommen.
    """
    for fach_row in reversed(fach_rows):
        ar, ac = resolve_anchor(ws, fach_row, col)
        if ar != fach_row:
            # Anker liegt in einer anderen Zeile – diese Zeile überspringen
            continue
        val = ws.cell(ar, ac).value
        if val is not None:
            return str(val)
    return None


def find_zustand_for_col(ws, zustand_rows: list[int], col: int) -> str | None:
    """Zustand-Label für Spalte col, mit Fallback auf höhere Zustand-Zeilen."""
    for zustand_row in reversed(zustand_rows):
        ar, ac = resolve_anchor(ws, zustand_row, col)
        if ar != zustand_row:
            continue
        val = ws.cell(ar, ac).value
        if val is not None:
            return str(val)
    return None


# ── Zeilen-Klassifikation ─────────────────────────────────────────────────────

def classify_row(ws, row: int) -> str:
    """'fach' | 'zustand' | 'jahrgang' | 'other'"""
    val = ws.cell(row, 1).value
    if val == "Fach":
        return "fach"
    if val == "Zustand":
        return "zustand"
    if isinstance(val, str) and re.match(r"Jahrgang\s+\d+", val):
        return "jahrgang"
    return "other"


def extract_grade(ws, row: int) -> int | None:
    val = ws.cell(row, 1).value
    m = re.match(r"Jahrgang\s+(\d+)", str(val)) if val else None
    return int(m.group(1)) if m else None


# ── Buch-Hilfsfunktionen ──────────────────────────────────────────────────────

def strip_hint(text: str) -> tuple[str, str | None]:
    """Trennt Serientitel-Hinweis in Klammern vom Fach-Namen.
    'Politik (eA)' → ('Politik', 'eA')
    'Deutsch'      → ('Deutsch', None)
    """
    m = re.match(r"^(.*?)\s*\((.+)\)\s*$", text.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return text.strip(), None


def load_grade_books(client: AusleiheClient, sy_id: str, bl_id: int) -> list[dict]:
    """Alle ausleihbaren Bücher einer Bücherliste (nur GET, gefiltert)."""
    try:
        detail = client.schoolyears.get_booklist(sy_id, bl_id)
    except NotFoundError:
        return []

    seen_isbns: set[str] = set()
    books: list[dict] = []
    for sec in detail.get("sections", []):
        for opt in sec.get("options", []):
            for item in opt.get("items", []):
                if not item.get("borrowable"):
                    continue
                sd = item.get("series_data", {}) or {}
                if (sd.get("fee") or 0) <= 0:
                    continue
                title = sd.get("title", "") or ""
                if "eBook" in title:
                    continue
                isbn = sd.get("isbn") or item.get("series") or ""
                if isbn in seen_isbns:
                    continue
                seen_isbns.add(isbn)
                books.append({
                    "isbn": isbn,
                    "title": title,
                    "subjects": sd.get("subjectsFlat", []) or [],
                })
    return books


def match_book(books: list[dict], subject: str, hint: str | None) -> dict | None:
    """Sucht passendes Buch nach Fach; Klammerzusatz schränkt bei Mehrfachtreffern ein."""
    candidates = [b for b in books if subject in b["subjects"]]
    if not candidates:
        return None
    if hint and len(candidates) > 1:
        narrowed = [b for b in candidates if hint.lower() in b["title"].lower()]
        if narrowed:
            return narrowed[0]
    return candidates[0]


# ── Anmelde-Zählung per Jahrgang ──────────────────────────────────────────────

def fetch_enrollment_counts_by_grade(
    client: AusleiheClient, sy_id: str
) -> tuple[dict[tuple[int, str], int], dict[tuple[int, str], int]]:
    """Zählt Anmeldungen und Bezahlungen pro (Jahrgang, ISBN).

    enrolled[(grade, isbn)] = Anzahl nicht-gelöschter Anmeldungen, die dieses Buch enthalten
    paid[(grade, isbn)]     = davon mit amountOpen == 0 (vollständig bezahlt)
    """
    enrollments = client.admin.get_enrollments(sy_id)
    enrolled: dict[tuple[int, str], int] = {}
    paid: dict[tuple[int, str], int] = {}

    for enr in enrollments:
        if enr.get("deleted_at"):
            continue
        grade = (enr.get("Booklist") or {}).get("grade")
        if grade is None:
            continue
        is_paid = enr.get("amountOpen", 1) == 0
        for item in enr.get("booklistItems", []):
            isbn = item.get("series")
            if not isbn:
                continue
            key = (grade, isbn)
            enrolled[key] = enrolled.get(key, 0) + 1
            if is_paid:
                paid[key] = paid.get(key, 0) + 1

    return enrolled, paid


# ── Hauptalgorithmus ──────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto-Befüllung von Angemeldet-/Bezahlt-Zellen anhand Excel-Struktur"
    )
    parser.add_argument("--dry-run", action="store_true", help="Keine Änderungen speichern")
    parser.add_argument("--schoolyear", help="Schuljahr-ID, z.B. 2025/2026")
    parser.add_argument("--excel", help="Excel-Dateiname (überschreibt config.json)")
    parser.add_argument("--sheet", help="Tabellenblatt-Name (überschreibt config.json)")
    args = parser.parse_args()

    print(f"Verbinde mit IServ ({os.environ.get('ISERV_DOMAIN', '?')})...")
    client = AusleiheClient()

    sy_id = args.schoolyear or client.schoolyears.get_current()["id"]
    print(f"Schuljahr: {sy_id}")

    # Excel-Datei und Tabellenblatt bestimmen
    with open(_HERE / "config.json", encoding="utf-8") as f:
        config = json.load(f)
    excel_filename = args.excel or config["excel_file"]
    sheet_name = args.sheet or config["sheet_name"]
    excel_path = _HERE / excel_filename
    print(f"Excel: {excel_path.name}  |  Blatt: {sheet_name}")

    # Bücherlisten für alle Jahrgänge laden
    print("Lade Bücherlisten...")
    booklists = client.schoolyears.get_booklists(sy_id)
    booklists_by_grade = {bl["grade"]: bl for bl in booklists if bl.get("grade") is not None}

    # Anmeldezahlen laden
    print("Lade Anmeldungen...")
    enrolled_counts, paid_counts = fetch_enrollment_counts_by_grade(client, sy_id)

    wb = load_workbook(str(excel_path))
    ws = wb[sheet_name]

    fach_rows: list[int] = []      # alle bisher gesehenen Fach-Zeilen (aufsteigend)
    zustand_rows: list[int] = []   # alle bisher gesehenen Zustand-Zeilen (aufsteigend)
    grade_books_cache: dict[int, list[dict]] = {}
    processed_anchors: set[str] = set()  # verhindert Doppelbearbeitung bei Zellenverbünden
    consecutive_other = 0
    changes: list[str] = []

    print("Analysiere Excel-Struktur...\n")

    for row in range(1, ws.max_row + 1):
        row_type = classify_row(ws, row)

        if row_type == "fach":
            fach_rows.append(row)
            consecutive_other = 0
            continue

        if row_type == "zustand":
            zustand_rows.append(row)
            consecutive_other = 0
            continue

        if row_type == "other":
            consecutive_other += 1
            if consecutive_other > 3:
                print(f"Zeile {row}: Abbruch – mehr als 3 nicht erkannte Zeilen in Folge.")
                break
            continue

        # Jahrgang-Zeile
        consecutive_other = 0
        grade = extract_grade(ws, row)
        if grade is None or not fach_rows:
            continue

        # Bücher für diesen Jahrgang laden (gecacht)
        if grade not in grade_books_cache:
            bl = booklists_by_grade.get(grade)
            if bl:
                print(f"  Lade Bücherliste Jahrgang {grade}...")
                grade_books_cache[grade] = load_grade_books(client, sy_id, bl["id"])
            else:
                print(f"  WARNUNG: Keine Bücherliste für Jahrgang {grade} im Schuljahr {sy_id}")
                grade_books_cache[grade] = []
        books = grade_books_cache[grade]

        # Alle Spalten der Jahrgang-Zeile durchsuchen
        for col in range(2, ws.max_column + 1):
            # Zustand-Label für diese Spalte bestimmen
            zustand_label = find_zustand_for_col(ws, zustand_rows, col)
            if zustand_label is None:
                continue
            zustand_norm = zustand_label.strip().lower()
            if zustand_norm not in ("angemeldet", "bezahlt"):
                continue

            # Fach-Label für diese Spalte bestimmen (mit Fallback auf höhere Fach-Zeilen)
            fach_val = find_fach_for_col(ws, fach_rows, col)
            if fach_val is None:
                continue

            subject, hint = strip_hint(fach_val)
            book = match_book(books, subject, hint)
            if book is None:
                continue

            # Ankerzelle der Jahrgang-Zeile bestimmen (Zellenverbund-Auflösung)
            ar, ac = resolve_anchor(ws, row, col)
            anchor_ref = f"{get_column_letter(ac)}{ar}"

            if anchor_ref in processed_anchors:
                continue  # Mehrjahresband oder bereits bearbeitet
            processed_anchors.add(anchor_ref)

            isbn = book["isbn"]
            key = (grade, isbn)
            if zustand_norm == "angemeldet":
                new_val = enrolled_counts.get(key, 0)
            else:  # bezahlt
                new_val = paid_counts.get(key, 0)

            old_val = ws[anchor_ref].value
            ws[anchor_ref] = new_val

            hint_str = f" ({hint})" if hint else ""
            changes.append(
                f"  {anchor_ref}: {old_val!r} -> {new_val!r}"
                f"  [{subject}{hint_str} Jg.{grade}, {book['title']}, {zustand_label}]"
            )

    # ── Ausgabe & Speichern ──────────────────────────────────────────────────
    print()
    if args.dry_run:
        print("-- DRY RUN: keine Datei wird gespeichert --")

    if changes:
        print(f"{len(changes)} Zelle(n) {'würden aktualisiert' if args.dry_run else 'aktualisiert'}:")
        for c in changes:
            print(c)
    else:
        print("Keine Änderungen.")

    if changes and not args.dry_run:
        wb.save(str(excel_path))
        print(f"\nGespeichert: {excel_path}")


if __name__ == "__main__":
    main()
