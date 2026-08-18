# Bücherlisten nach Fach — PDF-Export

Erzeugt aus den regulären Jahrgangs-Bücherlisten der IServ-Ausleihe-API eine
fachweise sortierte PDF-Bücherliste. Rein lesend (nur GET) — kein Schreibzugriff
auf die Produktionsdatenbank.

Es gibt keinen eigenen API-Endpunkt für diese Sicht. Das Skript holt alle
Jahrgangs-Bücherlisten eines Schuljahrs (`GET /schoolyears/:id/booklists/:bl_id`)
und stellt die Bücher clientseitig nach Fach neu zusammen — inklusive korrektem
Zusammenführen von Mehrjahresbänden (z.B. "Elemente Chemie 5/6"), die in
mehreren Jahrgangs-Bücherlisten gleichzeitig auftauchen.

## Schnellstart

```bash
# einmalig, falls noch nicht installiert:
pip install -e ".[buecherlisten]"

cd "buecherlisten-nach-fach"

# 1 PDF, neue Seite pro Fach (laufendes Schuljahr):
python3 generate_booklists.py --mode combined

# 1 PDF-Datei pro Fach:
python3 generate_booklists.py --mode split

# bestimmtes Schuljahr, eigener Zielordner:
python3 generate_booklists.py --schoolyear "2025/2026" --mode split --output-dir ~/Downloads
```

## Inhalt pro Fach

Zwei Tabellen — **Leihbare Bücher** (`borrowable=True`) und **Selbst
anzuschaffende Bücher** (`borrowable=False`: Arbeitshefte, "1x pro
Familie"-Anschaffungen, Digitallizenzen etc.) — mit den Spalten Klasse, Titel,
Verlag, ISBN, Neupreis, Leihgebühr.

- **ISBN** wird mit Bindestrichen dargestellt (`isbnlib.mask`, wie im
  Bestand-Tooling unter `bestand- und nachbestellungen/`) — die API liefert
  ISBNs immer ohne Trennzeichen, dafür gibt es keinen direkten Endpunkt.
- **Klasse:** Ein Buch, das in mehreren Jahrgängen angeboten wird
  (Mehrjahresband), erscheint einmal mit allen Klassen (z.B. "5/6"). Sortiert
  wird zuerst nach der untersten, dann nach der zweituntersten Klasse usw.
  Innerhalb gleicher Klassen-Kombination zusätzlich alphabetisch nach Titel.
- Bücher, die zu mehreren Fächern gehören (z.B. fächerübergreifende
  Formelsammlungen), erscheinen auf jeder betroffenen Fach-Seite/-Datei.

Voraussetzungen: `.env` mit IServ-Zugangsdaten im `ausleihe-api`-Root (siehe
Projekt-`CLAUDE.md`), sowie `reportlab` + `isbnlib` + `python-dotenv`
(`pip install -e ".[buecherlisten]"`).
