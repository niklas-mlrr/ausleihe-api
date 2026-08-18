#!/usr/bin/env python3
"""Bücherlisten eines Schuljahrs nach Fach aufbereitet als PDF.

Holt alle Bücherlisten (eine je Jahrgang) eines Schuljahrs über die
IServ-Ausleihe-API und stellt sie fachweise neu zusammen: pro Fach eine
Tabelle "Leihbare Bücher" und eine Tabelle "Selbst anzuschaffende Bücher"
(Spalten: Klasse, Titel, Verlag, ISBN, Neupreis, Leihgebühr). Bücher, die in
mehreren Jahrgängen angeboten werden (Mehrjahresbände), erscheinen einmal pro
Fach mit allen betroffenen Klassen (z.B. "5/6") und werden zuerst nach der
untersten, dann nach der zweituntersten Klasse einsortiert.

Es gibt für diesen Anwendungsfall keinen eigenen API-Endpunkt — die Zusammen-
stellung passiert clientseitig aus den regulären Bücherlisten-Daten
(GET /schoolyears/:id/booklists/:bl_id, siehe
~/wiki/wiki/30_projects/sba/ausleihe_api/api_reference.md). Die ISBN-Formatierung
mit Bindestrichen nutzt dieselbe isbnlib-Maskierung wie das Bestand-Tooling
unter "bestand- und nachbestellungen/"; auch dafür gibt es keinen API-Weg, die
Ausleihe-API liefert ISBNs immer ohne Trennzeichen.

Rein lesend (nur GET). Kein Schreibzugriff auf die IServ-Produktionsdatenbank.

Verwendung:
  python3 generate_booklists.py [--schoulyear 2026/2027] [--mode combined|split]
                                 [--output-dir PFAD]

  --schoolyear   Schuljahr wie "2026/2027" (Default: laufendes Schuljahr)
  --mode         combined = eine PDF-Datei mit einer neuen Seite pro Fach,
                            benannt "Bücherliste Fächer <Schuljahr>.pdf"
                 split    = eine PDF-Datei pro Fach,
                            benannt "Bücherliste <Fach> <Schuljahr>.pdf"
                 (Default: combined)
  --output-dir   Zielordner für die PDF(s) (Default: dieser Skriptordner)
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

_HERE = Path(__file__).parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv

load_dotenv(_ROOT / ".env")

from ausleihe import AusleiheClient  # noqa: E402
from ausleihe.exceptions import NotFoundError  # noqa: E402

try:
    import isbnlib as _isbnlib

    def format_isbn(isbn: str) -> str:
        try:
            masked = _isbnlib.mask(isbn)
            return masked if masked else isbn
        except Exception:
            return isbn
except ImportError:  # pragma: no cover

    def format_isbn(isbn: str) -> str:  # type: ignore[misc]
        return isbn


from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_LEFT  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TABLE_COLS = ["Klasse", "Titel", "Verlag", "ISBN", "Neupreis", "Leihgebühr"]
COL_WIDTHS = [16 * mm, 62 * mm, 32 * mm, 30 * mm, 22 * mm, 24 * mm]

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle(
    "FachTitel", parent=STYLES["Heading1"], fontSize=16, spaceAfter=2 * mm, alignment=TA_LEFT
)
SUBTITLE_STYLE = ParagraphStyle(
    "Schuljahr", parent=STYLES["Normal"], fontSize=10, textColor=colors.grey, spaceAfter=6 * mm
)
SECTION_STYLE = ParagraphStyle(
    "Abschnitt", parent=STYLES["Heading2"], fontSize=12, spaceBefore=4 * mm, spaceAfter=2 * mm
)
EMPTY_STYLE = ParagraphStyle("Leer", parent=STYLES["Normal"], fontSize=9, textColor=colors.grey)


def fmt_price(value: float | None) -> str:
    if value is None:
        return "–"
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "–"
    if value == 0:
        return "–"
    return f"{value:.2f}".replace(".", ",") + " €"


def fmt_grades(grades: tuple[int, ...]) -> str:
    return "/".join(str(g) for g in grades)


def collect_entries(client: AusleiheClient, schoolyear_id: str) -> dict[tuple[str, str], dict]:
    """Alle Bücherlisten-Items eines Schuljahrs, gruppiert nach (Fach, ISBN).

    Ein Buch, das in mehreren Jahrgangs-Bücherlisten desselben Fachs auftaucht
    (Mehrjahresband), wird zu einem Eintrag mit der Vereinigung der Klassen
    zusammengeführt — nicht anhand von series_data.gradesFlat (das ist ein
    globales Serien-Attribut und kann von den tatsächlichen Bücherlisten-
    Vorkommen abweichen, verifiziert 2026-08-18), sondern anhand der
    Bücherlisten-Jahrgänge, in denen das Item tatsächlich erscheint.
    """
    booklists = client.schoolyears.get_booklists(schoolyear_id)
    by_grade = {bl["grade"]: bl for bl in booklists if bl.get("grade") is not None}

    entries: dict[tuple[str, str], dict] = {}
    for grade in sorted(by_grade):
        bl = client.schoolyears.get_booklist(schoolyear_id, by_grade[grade]["id"])
        for section in bl.get("sections", []):
            for option in section.get("options", []):
                for item in option.get("items", []):
                    sd = item.get("series_data", {}) or {}
                    isbn = sd.get("isbn") or item.get("series")
                    if not isbn:
                        continue
                    subjects = sd.get("subjectsFlat") or ["(ohne Fach)"]
                    for subject in subjects:
                        key = (subject, isbn)
                        entry = entries.setdefault(
                            key,
                            {
                                "title": sd.get("title", "?"),
                                "publisher": sd.get("publisher", ""),
                                "price": sd.get("price"),
                                "fee": sd.get("fee"),
                                "borrowable": bool(item.get("borrowable")),
                                "grades": set(),
                            },
                        )
                        entry["grades"].add(grade)
    return entries


def build_subject_tables(entries: dict[tuple[str, str], dict]) -> dict[str, dict[str, list[dict]]]:
    """subject -> {"leih": [Zeilen...], "kauf": [Zeilen...]}, jeweils fertig sortiert."""
    by_subject: dict[str, dict[str, list[dict]]] = defaultdict(lambda: {"leih": [], "kauf": []})
    for (subject, isbn), e in entries.items():
        grades_sorted = tuple(sorted(e["grades"]))
        row = {
            "sort_key": (grades_sorted, e["title"].lower()),
            "klasse": fmt_grades(grades_sorted),
            "titel": e["title"],
            "verlag": e["publisher"],
            "isbn": format_isbn(isbn),
            "neupreis": fmt_price(e["price"]),
            "leihgebuehr": fmt_price(e["fee"]),
        }
        bucket = "leih" if e["borrowable"] else "kauf"
        by_subject[subject][bucket].append(row)

    for tables in by_subject.values():
        for bucket in ("leih", "kauf"):
            tables[bucket].sort(key=lambda r: r["sort_key"])
    return by_subject


def render_table(rows: list[dict]) -> Table:
    data = [TABLE_COLS] + [
        [r["klasse"], r["titel"], r["verlag"], r["isbn"], r["neupreis"], r["leihgebuehr"]] for r in rows
    ]
    table = Table(data, colWidths=COL_WIDTHS, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f3e46")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (4, 0), (5, -1), "RIGHT"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def subject_story(subject: str, tables: dict[str, list[dict]], schoolyear_id: str) -> list:
    story: list = [
        Paragraph(subject, TITLE_STYLE),
        Paragraph(f"Bücherliste – Schuljahr {schoolyear_id}", SUBTITLE_STYLE),
    ]

    story.append(Paragraph("Leihbare Bücher", SECTION_STYLE))
    if tables["leih"]:
        story.append(render_table(tables["leih"]))
    else:
        story.append(Paragraph("Keine leihbaren Bücher in diesem Fach.", EMPTY_STYLE))

    story.append(Paragraph("Selbst anzuschaffende Bücher", SECTION_STYLE))
    if tables["kauf"]:
        story.append(render_table(tables["kauf"]))
    else:
        story.append(Paragraph("Keine selbst anzuschaffenden Bücher in diesem Fach.", EMPTY_STYLE))

    return story


def write_pdf(path: Path, story: list, title: str) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=title,
    )
    doc.build(story)


def sanitize_filename(name: str) -> str:
    return name.replace("/", "-")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bücherlisten nach Fach als PDF.")
    parser.add_argument("--schoolyear", default=None, help='Schuljahr, z.B. "2026/2027" (Default: laufendes)')
    parser.add_argument(
        "--mode", choices=["combined", "split"], default="combined",
        help="combined = 1 PDF mit Seite pro Fach, split = 1 PDF je Fach (Default: combined)",
    )
    parser.add_argument("--output-dir", default=None, help="Zielordner (Default: dieser Skriptordner)")
    args = parser.parse_args()

    client = AusleiheClient(allow_writes=False)

    schoolyear_id = args.schoolyear or client.schoolyears.get_current()["id"]
    try:
        entries = collect_entries(client, schoolyear_id)
    except NotFoundError:
        print(f"Fehler: Schuljahr nicht gefunden: {schoolyear_id}", file=sys.stderr)
        sys.exit(1)

    by_subject = build_subject_tables(entries)
    subjects = sorted(by_subject, key=str.casefold)
    if not subjects:
        print(f"Keine Bücher für Schuljahr {schoolyear_id} gefunden.", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.output_dir) if args.output_dir else _HERE
    out_dir.mkdir(parents=True, exist_ok=True)
    sy_label = sanitize_filename(schoolyear_id)

    if args.mode == "combined":
        story: list = []
        for i, subject in enumerate(subjects):
            if i > 0:
                story.append(PageBreak())
            story.extend(subject_story(subject, by_subject[subject], schoolyear_id))
        out_path = out_dir / f"Bücherliste Fächer {sy_label}.pdf"
        write_pdf(out_path, story, title=f"Bücherliste Fächer {schoolyear_id}")
        print(f"PDF gespeichert: {out_path}")
    else:
        for subject in subjects:
            story = subject_story(subject, by_subject[subject], schoolyear_id)
            out_path = out_dir / f"Bücherliste {subject} {sy_label}.pdf"
            write_pdf(out_path, story, title=f"Bücherliste {subject} {schoolyear_id}")
            print(f"PDF gespeichert: {out_path}")


if __name__ == "__main__":
    main()
