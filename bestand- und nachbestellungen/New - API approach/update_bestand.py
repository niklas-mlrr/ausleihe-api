#!/usr/bin/env python3
"""Aktualisiert die 'Bestand'-Zellen in der Excel-Datei mit Daten aus der Ausleihe-API.

Verwendung:
    python3 update_bestand.py [--dry-run]

Liest config.json aus demselben Verzeichnis. Alle Pfade sind relativ zur
Position dieser Datei – das Skript ist vollständig selbstständig.

'Angemeldet'-Zellen werden noch nicht befüllt (Admin-API-Endpunkt ausstehend).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

from openpyxl import load_workbook

from ausleihe import AusleiheClient, NotFoundError


def load_config() -> dict:
    path = _HERE / "config.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bestand-Zellen in Excel aktualisieren")
    parser.add_argument("--dry-run", action="store_true", help="Keine Änderungen speichern")
    args = parser.parse_args()

    config = load_config()
    excel_path = _HERE / config["excel_file"]
    mappings: list[dict] = config["mappings"]

    bestand_mappings = [(m["isbn"], m["bestand_cell"]) for m in mappings if "bestand_cell" in m]
    angemeldet_mappings = [(m["isbn"], m["angemeldet_cell"]) for m in mappings if "angemeldet_cell" in m]
    unique_isbns = {isbn for isbn, _ in bestand_mappings}

    print(f"Verbinde mit IServ ({os.environ.get('ISERV_DOMAIN', '?')})...")
    client = AusleiheClient()
    print(f"Lade {len(unique_isbns)} Serien von der API...")

    series_total: dict[str, int] = {}
    series_title: dict[str, str] = {}
    for isbn in sorted(unique_isbns):
        try:
            s = client.series.get_by_isbn(isbn)
            if s.total is not None:
                series_total[isbn] = s.total
                series_title[isbn] = s.title
            else:
                print(f"  WARNUNG: {isbn} — 'total' fehlt in API-Antwort")
        except NotFoundError:
            print(f"  WARNUNG: {isbn} — nicht gefunden (abgelöste Serie?)")
        except Exception as e:
            print(f"  FEHLER:   {isbn} — {e}")

    wb = load_workbook(str(excel_path))
    ws = wb[config["sheet_name"]]

    changed: list[tuple[str, object, int, str]] = []
    unchanged: int = 0
    not_found: list[str] = []

    for isbn, cell in bestand_mappings:
        if isbn not in series_total:
            not_found.append(f"{cell} (ISBN {isbn})")
            continue
        old = ws[cell].value
        new = series_total[isbn]
        if old != new:
            ws[cell] = new
            changed.append((cell, old, new, series_title[isbn]))
        else:
            unchanged += 1

    print()
    if args.dry_run:
        print("-- DRY RUN: keine Datei wird gespeichert --")

    if changed:
        if not args.dry_run:
            wb.save(str(excel_path))
        print(f"{len(changed)} Zelle(n) {'würden aktualisiert' if args.dry_run else 'aktualisiert'}:")
        for cell, old, new, title in changed:
            print(f"  {cell}: {old} -> {new}  [{title}]")
    else:
        print("Keine Änderungen.")

    if unchanged:
        print(f"{unchanged} Zelle(n) bereits aktuell.")

    if not_found:
        print(f"\n{len(not_found)} Zelle(n) übersprungen (ISBN nicht in API):")
        for s in not_found:
            print(f"  {s}")

    if angemeldet_mappings:
        cells = ", ".join(cell for _, cell in angemeldet_mappings)
        print(f"\nHINWEIS: {len(angemeldet_mappings)} 'Angemeldet'-Zellen nicht aktualisiert ({cells}).")
        print("  Benötigt Admin-API (get_enrollments) — noch nicht implementiert.")


if __name__ == "__main__":
    main()
