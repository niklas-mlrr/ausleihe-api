#!/usr/bin/env python3
"""Bücherlisten eines Schuljahrs nach Fach aufbereitet als PDF.

Holt alle Bücherlisten (eine je Jahrgang) eines Schuljahrs über die
IServ-Ausleihe-API und stellt sie fachweise neu zusammen: pro Fach eine
Tabelle "Leihbare Bücher" (Spalten Klasse, Titel, Verlag, ISBN, Neupreis,
Leihgebühr) und eine Tabelle "Selbst anzuschaffende Bücher" (dieselben Spalten
ohne Leihgebühr — genau wie in den offiziellen IServ-Bücherlisten-PDFs, an
deren Aufmachung sich dieses Layout orientiert). Bücher, die in mehreren
Jahrgängen angeboten werden (Mehrjahresbände), erscheinen einmal pro Fach mit
allen betroffenen Klassen (z.B. "5, 6") und werden zuerst nach der untersten,
dann nach der zweituntersten Klasse einsortiert.

Spaltenbreiten: Klasse/ISBN/Neupreis/Leihgebühr brechen nie um. Titel und
Verlag dürfen umbrechen, tun es aber nur, wenn der Inhalt nicht einzeilig in
die Tabellenbreite passt — dann wird der Platz zwischen beiden so aufgeteilt,
dass die Tabelle insgesamt möglichst wenig Zeilen braucht ("Leihgebühr" wird
dabei zu "Leihgeb.", "Klasse" bei Bedarf zu "Kl."). Alle Spaltenzwischenräume
sind danach gleich breit, jede Spalte ist maximal so breit wie ihr
tatsächlich benötigter Inhalt (Details: `buecherlisten_layout.md` im Wiki).

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
                                 [--subjects "Fach1" "Fach2" ...] [--list-subjects]
                                 [--output-dir PFAD]

  --schoolyear     Schuljahr wie "2026/2027" (Default: laufendes Schuljahr)
  --mode           combined = eine PDF-Datei mit einer neuen Seite pro Fach,
                              benannt "Bücherliste Fächer <Schuljahr>.pdf"
                   split    = eine PDF-Datei pro Fach,
                              benannt "Bücherliste <Fach> <Schuljahr>.pdf"
                   (Default: combined)
  --subjects       Nur diese Fächer aufnehmen (ein oder mehrere Namen, exakt
                    wie in der Bücherliste, z.B. --subjects Deutsch Mathematik).
                    Default: alle Fächer, die im Schuljahr vorkommen.
  --list-subjects  Nur die verfügbaren Fächer des Schuljahrs auflisten und
                    beenden (keine PDF-Erzeugung).
  --output-dir     Zielordner für die PDF(s) (Default: dieser Skriptordner)
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime
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
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.pdfbase.pdfmetrics import stringWidth  # noqa: E402
from reportlab.pdfgen.canvas import Canvas  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    BaseDocTemplate,
    Flowable,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Table,
    TableStyle,
)

# Schulname für die Fußzeile — an der Aufmachung der offiziellen IServ-
# Bücherlisten-PDFs orientiert (dort im Footer geführt).
SCHOOL_NAME = "Tilman-Riemenschneider-Gymnasium Osterode am Harz"

# ── Maße aus der offiziellen IServ-Bücherliste ───────────────────────────────
# Alle Werte unten sind aus "Bücherliste Jahrgang 5.pdf" ausgemessen
# (pdfplumber, 2026-08-18) und bewusst als absolute Punkt-Angaben gepflegt:
# Kopfbereich, Überschrift und Tabellen sollen deckungsgleich mit dem Original
# sitzen. Alles unterhalb der Tabellen (Fußzeile) ist davon ausgenommen.
PAGE_W, PAGE_H = A4

LEFT_MARGIN = 72.0                          # Textkante links (Original: x0 = 72.00)
RIGHT_EDGE = 537.28                         # Textkante rechts (Original: x1 = 537.28)
RIGHT_MARGIN = PAGE_W - RIGHT_EDGE          # = 58.0 (Original ist asymmetrisch)
CONTENT_WIDTH = RIGHT_EDGE - LEFT_MARGIN    # = 465.28 — auch die Tabellenbreite

# Grundlinien (Baselines) gemessen vom Seitenoberrand.
HEADER_LABEL_FONT, HEADER_LABEL_SIZE = "Helvetica", 8.0
HEADER_LABEL_BASELINE = PAGE_H - 45.74      # "Liste für" / "gültig für"
HEADER_VALUE_FONT, HEADER_VALUE_SIZE = "Helvetica-Bold", 12.0
HEADER_VALUE_BASELINE = PAGE_H - 56.02      # "Schuljahr 26/27" / "<Fach>"
TITLE_FONT, TITLE_SIZE = "Helvetica-Bold", 24.0
TITLE_BASELINE = PAGE_H - 105.73            # "Bücherliste <Fach>"

# Der Fließtext-Rahmen beginnt oben auf der Seite; der Kopf-/Titelblock wird
# absolut positioniert gezeichnet und reserviert nur seine Höhe (siehe
# SubjectHeading). INTRO_TOP ist die Oberkante des Einleitungstexts.
FRAME_TOP = PAGE_H - 30.0
INTRO_TOP = 714.0
HEADING_BLOCK_HEIGHT = FRAME_TOP - INTRO_TOP
BOTTOM_MARGIN = 18 * mm
# Die Fußzeile bleibt bewusst schmaler eingerückt als der Inhalt (wie im
# Original): sonst kollidiert der linke Fußzeilentext mit dem zentrierten.
FOOTER_MARGIN = 15 * mm

ACCENT_COLOR = colors.Color(0.6627, 0.2667, 0.2588)  # Original-Rot der Abschnittstitel
RULE_COLOR = colors.black                            # Linie unter der Kopfzeile (1.0pt schwarz)
ROW_RULE_COLOR = colors.Color(0.6667, 0.6667, 0.6667)  # Zeilentrenner (1.0pt grau)
GREY = colors.HexColor("#666666")

# Tabellen-Typografie exakt wie im Original: durchgehend Helvetica 10, nur die
# ISBN-Werte 8pt; Kopfzeile ist ebenfalls Helvetica 10 (nicht fett).
BODY_FONT = "Helvetica"
HEADER_FONT = "Helvetica"
CELL_FONT_SIZE = 10.0
ISBN_FONT_SIZE = 8.0
# Mindestbreite für Titel/Verlag beim Aufteilen des Restplatzes, damit keine
# der beiden Spalten auf ein einzelnes-Zeichen-pro-Zeile schrumpft.
MIN_WRAP_COL = 20 * mm
# Schrittweite der Breiten-Suche für die Titel/Verlag-Aufteilung (siehe
# _split_titel_verlag). 1pt ist für Tabellen dieser Größe schnell genug.
SPLIT_SEARCH_STEP = 1.0
# Mindestabstand zwischen zwei Spalten (14pt = 7pt je Seite), auch wenn der
# Inhalt die Tabellenbreite fast ausfüllt — sonst kann der rechnerisch
# gleichmäßig verteilte Rest pro Lücke gegen 0 gehen und Text ohne sichtbaren
# Abstand aneinanderstoßen (beobachtet 2026-08-18, "Klasse"-Wert direkt vor
# dem Titel).
MIN_GAP = 14.0

STYLES = getSampleStyleSheet()
INTRO_STYLE = ParagraphStyle(
    "Intro", parent=STYLES["Normal"], fontName=BODY_FONT, fontSize=10, leading=12.5,
    textColor=colors.black, spaceAfter=6 * mm,
)
SECTION_STYLE = ParagraphStyle(
    "Abschnitt", parent=STYLES["Heading2"], fontName="Helvetica-Bold", fontSize=16,
    textColor=ACCENT_COLOR, spaceBefore=6 * mm, spaceAfter=3 * mm, leading=19,
)
EMPTY_STYLE = ParagraphStyle("Leer", parent=STYLES["Normal"], fontSize=9, textColor=GREY)

# Titel/Verlag brechen um (Paragraph); alle anderen Spalten bleiben Klartext
# in exakt passend berechneten Breiten (siehe render_table). splitLongWords=0
# verhindert, dass reportlab ein Wort mitten im Zeichen umbricht, wenn die
# zugewiesene Breite durch Rundung minimal knapper ist als das Wort selbst
# (beobachtet 2026-08-18, "Westermann" bei Erdkunde) — ein Wort, das nicht
# passt, läuft dann lieber minimal über, statt aufgetrennt zu werden.
CELL_STYLE = ParagraphStyle(
    "Zelle", parent=STYLES["Normal"], fontName=BODY_FONT, fontSize=CELL_FONT_SIZE, leading=11.5,
    splitLongWords=0,
)


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


def short_schoolyear(schoolyear_id: str) -> str:
    # "2026/2027" -> "26/27", wie im Kopfbereich der offiziellen
    # IServ-Bücherlisten-PDFs ("Liste für / Schuljahr 26/27").
    parts = schoolyear_id.split("/")
    if len(parts) == 2 and all(p.isdigit() for p in parts):
        return "/".join(p[-2:] for p in parts)
    return schoolyear_id


def fmt_grades(grades: tuple[int, ...]) -> str:
    # Komma + Leerzeichen statt "/": erlaubt Zeilenumbruch in der schmalen
    # Klasse-Spalte, wenn ein Mehrjahresband viele Klassen abdeckt.
    return ", ".join(str(g) for g in grades)


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


# Kleiner Sicherheitszuschlag auf jede berechnete Inhaltsbreite: reportlabs
# Paragraph-Layout kann bei der Wortabstands-/Kerning-Behandlung minimal von
# unserer stringWidth-Schätzung abweichen. Ohne Puffer reicht das, um ein
# Wort exakt an der Kante nicht mehr passen zu lassen — mit splitLongWords=0
# (siehe CELL_STYLE) würde es dann zwar nicht mitten im Wort umgebrochen,
# aber minimal über den Zellenrand hinausragen.
WIDTH_EPSILON = 0.5


def _raw_width(header: str, values: list[str], *, value_size: float = CELL_FONT_SIZE) -> float:
    """Reine Inhaltsbreite (kein Zellenpolster) = längster Kopf- oder Zellentext.

    "Länge" heißt hier immer gemessene Textbreite (`stringWidth`), nie
    Zeichenanzahl — ein kurzes "M" ist breiter als ein langes "iii".
    """
    widths = [stringWidth(header, HEADER_FONT, CELL_FONT_SIZE)]
    widths += [stringWidth(v, BODY_FONT, value_size) for v in values]
    return (max(widths) + WIDTH_EPSILON) if widths else 0.0


def _wrap_lines(text: str, width: float, *, font: str = BODY_FONT, size: float = CELL_FONT_SIZE) -> list[str]:
    """Greedy Wortumbruch wie reportlabs Paragraph (Standard, ohne Silbentrennung).

    Bricht ausschließlich an Leerzeichen — ein einzelnes Wort, das breiter als
    `width` ist, bleibt trotzdem als Ganzes auf einer Zeile (siehe Gotcha zu
    splitLongWords bei CELL_STYLE)."""
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _wrap_info(text: str, width: float, *, font: str = BODY_FONT, size: float = CELL_FONT_SIZE) -> tuple[int, float]:
    """(Zeilenzahl, breiteste tatsächlich benötigte Zeile) beim Umbruch auf `width`."""
    lines = _wrap_lines(text, width, font=font, size=size)
    max_line_w = max((stringWidth(line, font, size) for line in lines), default=0.0)
    return len(lines), max_line_w + WIDTH_EPSILON


def _max_word_width(values: list[str], *, font: str = BODY_FONT, size: float = CELL_FONT_SIZE) -> float:
    """Breitestes einzelnes Wort über alle Werte — `_wrap_lines` bricht nie
    innerhalb eines Worts um, also kann eine Spalte nie schmaler werden als
    das breiteste unteilbare Wort, das in ihr vorkommt."""
    widest = 0.0
    for v in values:
        for word in v.split():
            widest = max(widest, stringWidth(word, font, size))
    return widest + WIDTH_EPSILON if widest else 0.0


def _split_titel_verlag(
    titel_vals: list[str], verlag_vals: list[str], available: float,
) -> tuple[float, float, float, float]:
    """Titel/Verlag-Breite so wählen, dass die Tabelle insgesamt am wenigsten
    Zeilen braucht (= am kleinsten ist); bei Gleichstand die Aufteilung, die
    zusätzlich am wenigsten Breite tatsächlich braucht.

    Rückgabe: (titel_budget, verlag_budget, titel_actual, verlag_actual) —
    *_actual ist die nach dem Umbruch bei diesem Budget tatsächlich breiteste
    Zeile (meist etwas schmaler als das Budget, siehe "eine Spalte nur
    maximal so lang wie der längste Inhalt einer Zeile").
    """
    if not titel_vals:
        return 0.0, 0.0, 0.0, 0.0

    # Kein Budget darf unter das breiteste unteilbare Wort der jeweiligen
    # Spalte fallen — sonst wird die tatsächlich gerenderte Zeile breiter als
    # das der anderen Spalte zugestandene Budget, und die Tabelle läuft über
    # die rechte Kante hinaus (beobachtet 2026-08-18, "Bibliographisches").
    min_titel = max(MIN_WRAP_COL, _max_word_width(titel_vals))
    min_verlag = max(MIN_WRAP_COL, _max_word_width(verlag_vals))

    if available <= min_titel + min_verlag:
        # Nicht genug Platz für beide Mindestbreiten — beide bekommen exakt
        # ihr Minimum; die Tabelle kann dann geringfügig breiter werden als
        # CONTENT_WIDTH (unvermeidbar bei einem einzelnen sehr breiten Wort).
        return min_titel, min_verlag, min_titel, min_verlag

    lo, hi = min_titel, available - min_verlag
    best: tuple[tuple[int, float], float, float, float] | None = None
    w = lo
    while w <= hi + 1e-6:
        verlag_w = available - w
        total_lines = 0
        max_titel_line = 0.0
        max_verlag_line = 0.0
        for t, v in zip(titel_vals, verlag_vals):
            lt, mt = _wrap_info(t, w)
            lv, mv = _wrap_info(v, verlag_w)
            total_lines += max(lt, lv)
            max_titel_line = max(max_titel_line, mt)
            max_verlag_line = max(max_verlag_line, mv)
        key = (total_lines, max_titel_line + max_verlag_line)
        if best is None or key < best[0]:
            best = (key, w, max_titel_line, max_verlag_line)
        w += SPLIT_SEARCH_STEP

    assert best is not None
    _, titel_w, titel_actual, verlag_actual = best
    return titel_w, available - titel_w, titel_actual, verlag_actual


def render_table(rows: list[dict], *, with_fee: bool) -> Table:
    isbn_idx, neupreis_idx = 3, 4
    n_cols = 6 if with_fee else 5
    n_gaps = n_cols - 1

    # Für jeden der n_gaps Zwischenräume wird vorab MIN_GAP reserviert, bevor
    # Spaltenbreiten überhaupt berechnet werden — sonst kann der nach Schritt 3
    # rechnerisch übrige Platz pro Lücke gegen 0 gehen, wenn der Inhalt die
    # Tabellenbreite fast ausfüllt (beobachtet 2026-08-18: "12Duden..." ohne
    # sichtbaren Abstand). effective_width ist das Budget, mit dem Schritt 1/2
    # rechnen — der danach ermittelte Gesamtinhalt passt dadurch garantiert
    # mit mindestens MIN_GAP Luft pro Lücke in CONTENT_WIDTH.
    effective_width = CONTENT_WIDTH - MIN_GAP * n_gaps

    klasse_vals = [r["klasse"] for r in rows]
    titel_vals = [r["titel"] for r in rows]
    verlag_vals = [r["verlag"] for r in rows]
    isbn_vals = [r["isbn"] for r in rows]
    neupreis_vals = [r["neupreis"] for r in rows]
    leihgebuehr_vals = [r["leihgebuehr"] for r in rows] if with_fee else []

    klasse_header = "Klasse"
    leihgebuehr_header = "Leihgebühr"

    # 1) Passt alles einzeilig (jede Spalte auf ihre natürliche Breite,
    #    Titel/Verlag inklusive) in die Tabellenbreite? Dann muss nichts
    #    umbrechen und nichts abgekürzt werden.
    isbn_w = _raw_width("ISBN", isbn_vals, value_size=ISBN_FONT_SIZE)
    neupreis_w = _raw_width("Neupreis", neupreis_vals)
    natural_klasse_w = _raw_width(klasse_header, klasse_vals)
    natural_leihgebuehr_w = _raw_width(leihgebuehr_header, leihgebuehr_vals) if with_fee else 0.0
    natural_titel_w = _raw_width("Titel", titel_vals)
    natural_verlag_w = _raw_width("Verlag", verlag_vals)
    natural_total = (
        natural_klasse_w + natural_titel_w + natural_verlag_w + isbn_w + neupreis_w + natural_leihgebuehr_w
    )

    if natural_total <= effective_width:
        klasse_w, titel_w, verlag_w, leihgebuehr_w = (
            natural_klasse_w, natural_titel_w, natural_verlag_w, natural_leihgebuehr_w,
        )
    else:
        # 2) Reicht nicht — zuerst Platz durch Abkürzen der Kopfzeilen
        #    zurückgewinnen: "Leihgebühr" wird immer zu "Leihgeb."; "Klasse"
        #    nur, wenn der Spaltentitel selbst breiter ist als der breiteste
        #    Klassen-Wert (sonst würde die Abkürzung nichts bringen).
        if with_fee:
            leihgebuehr_header = "Leihgeb."
        klasse_data_w = max((stringWidth(v, BODY_FONT, CELL_FONT_SIZE) for v in klasse_vals), default=0.0)
        if stringWidth(klasse_header, HEADER_FONT, CELL_FONT_SIZE) > klasse_data_w:
            klasse_header = "Kl."
        klasse_w = _raw_width(klasse_header, klasse_vals)
        leihgebuehr_w = _raw_width(leihgebuehr_header, leihgebuehr_vals) if with_fee else 0.0

        fixed_w = klasse_w + isbn_w + neupreis_w + leihgebuehr_w
        available_tv = effective_width - fixed_w
        _, _, titel_w, verlag_w = _split_titel_verlag(titel_vals, verlag_vals, available_tv)

        # 2b) Abkürzungen zurücknehmen, wenn nach der Titel/Verlag-Aufteilung
        #     wieder Platz dafür ist — zuerst "Klasse", danach (mit dem dann
        #     schon etwas größeren Gesamtinhalt) "Leihgebühr". Erst danach
        #     wird verteilt, damit die dadurch länger gewordenen Spalten in
        #     der Gleichverteilung berücksichtigt sind.
        total_now = klasse_w + titel_w + verlag_w + isbn_w + neupreis_w + leihgebuehr_w
        if klasse_header == "Kl.":
            full_klasse_w = _raw_width("Klasse", klasse_vals)
            if total_now + (full_klasse_w - klasse_w) <= effective_width:
                total_now += full_klasse_w - klasse_w
                klasse_w = full_klasse_w
                klasse_header = "Klasse"
        if with_fee and leihgebuehr_header == "Leihgeb.":
            full_leihgebuehr_w = _raw_width("Leihgebühr", leihgebuehr_vals)
            if total_now + (full_leihgebuehr_w - leihgebuehr_w) <= effective_width:
                total_now += full_leihgebuehr_w - leihgebuehr_w
                leihgebuehr_w = full_leihgebuehr_w
                leihgebuehr_header = "Leihgebühr"

    # 3) Restplatz gleichmäßig auf alle Spaltenzwischenräume verteilen —
    #    jede Spalte bleibt exakt so breit wie ihr tatsächlich benötigter
    #    Inhalt (keine Spalte länger als der längste Inhalt einer Zeile).
    #    Dank effective_width in Schritt 1/2 ist gap hier immer >= MIN_GAP.
    total_content = klasse_w + titel_w + verlag_w + isbn_w + neupreis_w + leihgebuehr_w
    gap = max(CONTENT_WIDTH - total_content, 0.0) / n_gaps if n_gaps else 0.0
    half_gap = gap / 2

    # colWidths braucht die VOLLE Spaltenbreite inkl. ihres Anteils an der
    # Lücke (reportlab zieht das TableStyle-Padding von colWidth ab, um die
    # Textfläche zu bestimmen — reine Inhaltsbreite hier würde bei jeder
    # Spalte außer der ersten/letzten ins Negative laufen).
    content_widths = [klasse_w, titel_w, verlag_w, isbn_w, neupreis_w]
    if with_fee:
        content_widths.append(leihgebuehr_w)
    col_widths = [
        w + (0.0 if i == 0 else half_gap) + (0.0 if i == n_cols - 1 else half_gap)
        for i, w in enumerate(content_widths)
    ]

    cols = [klasse_header, "Titel", "Verlag", "ISBN", "Neupreis"]
    if with_fee:
        cols.append(leihgebuehr_header)

    data = [list(cols)]
    for r in rows:
        line = [
            r["klasse"],
            Paragraph(r["titel"], CELL_STYLE),
            Paragraph(r["verlag"], CELL_STYLE),
            r["isbn"],
            r["neupreis"],
        ]
        if with_fee:
            line.append(r["leihgebuehr"])
        data.append(line)

    last_row = len(data) - 1
    # Tabellenbild wie im Original: keine Füllfarben, kein Gitternetz, 1.0pt
    # schwarze Linie unter der Kopfzeile, 1.0pt graue Trennlinie unter jeder
    # Datenzeile. Klasse/Titel/Verlag/ISBN linksbündig, Neupreis/Leihgebühr
    # rechtsbündig (nur Datenzeilen — die Kopfzeile bleibt linksbündig).
    style = [
        ("FONTNAME", (0, 0), (-1, 0), HEADER_FONT),
        ("FONTNAME", (0, 1), (-1, -1), BODY_FONT),
        ("FONTSIZE", (0, 0), (-1, -1), CELL_FONT_SIZE),
        ("FONTSIZE", (isbn_idx, 1), (isbn_idx, -1), ISBN_FONT_SIZE),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("ALIGN", (neupreis_idx, 1), (-1, -1), "RIGHT"),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, RULE_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        # Gleicher Abstand zwischen allen Spalten: jede Innenkante bekommt die
        # halbe Lücke, außen (erste/letzte Spalte) bleibt 0 — Tabelle fluchtet
        # weiterhin links mit "Liste für"/Überschrift, rechts mit "gültig für".
        ("LEFTPADDING", (0, 0), (-1, -1), half_gap),
        ("RIGHTPADDING", (0, 0), (-1, -1), half_gap),
        ("LEFTPADDING", (0, 0), (0, -1), 0),
        ("RIGHTPADDING", (-1, 0), (-1, -1), 0),
    ]
    if last_row >= 1:
        style.append(("LINEBELOW", (0, 1), (-1, last_row), 1.0, ROW_RULE_COLOR))
    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle(style))
    return table


class SubjectHeading(Flowable):
    """Kopfbereich + Überschrift an den exakten Positionen des Originals.

    Die drei Textzeilen werden **absolut** auf der Seite gezeichnet (Baselines
    und x-Kanten aus der offiziellen IServ-Bücherliste ausgemessen), nicht im
    normalen Textfluss positioniert. Der Flowable reserviert im Fluss nur die
    Höhe des Blocks, damit der Einleitungstext darunter beginnt.
    """

    def __init__(self, schoolyear_id: str, subject: str) -> None:
        super().__init__()
        self.schoolyear_id = schoolyear_id
        self.subject = subject
        self.width = CONTENT_WIDTH
        self.height = HEADING_BLOCK_HEIGHT

    def draw(self) -> None:
        c = self.canv
        # draw() zeichnet in lokalen Koordinaten — Ursprung auf die absoluten
        # Seitenkoordinaten zurückrechnen, damit der Block unabhängig von
        # seiner Position im Fluss immer exakt gleich sitzt.
        origin_x, origin_y = c.absolutePosition(0, 0)
        dx, dy = -origin_x, -origin_y

        c.saveState()
        c.setFillColor(colors.black)
        c.setFont(HEADER_LABEL_FONT, HEADER_LABEL_SIZE)
        c.drawString(dx + LEFT_MARGIN, dy + HEADER_LABEL_BASELINE, "Liste für")
        c.drawRightString(dx + RIGHT_EDGE, dy + HEADER_LABEL_BASELINE, "gültig für")

        c.setFont(HEADER_VALUE_FONT, HEADER_VALUE_SIZE)
        c.drawString(
            dx + LEFT_MARGIN, dy + HEADER_VALUE_BASELINE,
            f"Schuljahr {short_schoolyear(self.schoolyear_id)}",
        )
        c.drawRightString(dx + RIGHT_EDGE, dy + HEADER_VALUE_BASELINE, self.subject)

        c.setFont(TITLE_FONT, TITLE_SIZE)
        c.drawString(dx + LEFT_MARGIN, dy + TITLE_BASELINE, f"Bücherliste {self.subject}")
        c.restoreState()


def subject_story(subject: str, tables: dict[str, list[dict]], schoolyear_id: str) -> list:
    story: list = [
        SubjectHeading(schoolyear_id, subject),
        Paragraph(
            f"Die folgenden Bücher können für das Fach {subject} über die Schule ausgeliehen werden. "
            "Bücher, die selbst anzuschaffen sind, werden gesondert in der zweiten Tabelle ausgewiesen.",
            INTRO_STYLE,
        ),
    ]

    story.append(Paragraph("Leihbare Bücher", SECTION_STYLE))
    if tables["leih"]:
        story.append(render_table(tables["leih"], with_fee=True))
    else:
        story.append(Paragraph("Keine leihbaren Bücher in diesem Fach.", EMPTY_STYLE))

    story.append(Paragraph("Selbst anzuschaffende Bücher", SECTION_STYLE))
    if tables["kauf"]:
        story.append(render_table(tables["kauf"], with_fee=False))
    else:
        story.append(Paragraph("Keine selbst anzuschaffenden Bücher in diesem Fach.", EMPTY_STYLE))

    return story


def make_footer(center_text: str):
    """onPage-Callback: Fußzeile ähnlich den offiziellen IServ-PDFs
    (Erstellungsdatum links, Seitenzahl rechts, Schule+Kontext mittig)."""
    generated = datetime.now().strftime("%d.%m.%Y")

    def _draw(c: Canvas, doc: BaseDocTemplate) -> None:
        width, _height = A4
        left_text = f"Erstellt am {generated}"
        right_text = f"Seite {doc.page}"
        base_fs, min_fs, gap = 7.5, 6.0, 4

        c.saveState()
        c.setFillColor(GREY)
        left_end = FOOTER_MARGIN + c.stringWidth(left_text, "Helvetica", base_fs)
        right_start = width - FOOTER_MARGIN - c.stringWidth(right_text, "Helvetica", base_fs)
        # Zentrierter Text steht bei width/2 — maßgeblich ist der KLEINERE der
        # beiden Abstände zur linken/rechten Fußzeile, nicht die Summe (sonst
        # ragt er bei asymmetrischen Rand-Texten trotzdem in eine Seite hinein).
        max_half_width = max(min(width / 2 - left_end, right_start - width / 2) - gap, 10)

        # Der mittige Schule+Kontext-Text kann bei langen Fachnamen mit dem
        # linken/rechten Fußzeilentext kollidieren (beobachtet 2026-08-18,
        # z.B. "Werte und Normen") — Schriftgröße notfalls schrittweise
        # verkleinern, bis er in die verbleibende Lücke passt.
        center_fs = base_fs
        while center_fs > min_fs and c.stringWidth(center_text, "Helvetica", center_fs) / 2 > max_half_width:
            center_fs -= 0.25

        c.setFont("Helvetica", base_fs)
        c.drawString(FOOTER_MARGIN, 10 * mm, left_text)
        c.drawRightString(width - FOOTER_MARGIN, 10 * mm, right_text)
        c.setFont("Helvetica", center_fs)
        c.drawCentredString(width / 2, 10 * mm, center_text)
        c.restoreState()

    return _draw


def write_pdf(path: Path, story: list, title: str, footer_center: str) -> None:
    # BaseDocTemplate statt SimpleDocTemplate: dessen Frame hat 6pt Innenrand,
    # der den Inhalt gegenüber den Seitenrändern verschiebt. Hier soll der Text
    # exakt auf LEFT_MARGIN/RIGHT_EDGE sitzen → Frame-Padding auf 0.
    doc = BaseDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=LEFT_MARGIN,
        rightMargin=RIGHT_MARGIN,
        topMargin=PAGE_H - FRAME_TOP,
        bottomMargin=BOTTOM_MARGIN,
        title=title,
    )
    frame = Frame(
        LEFT_MARGIN, BOTTOM_MARGIN, CONTENT_WIDTH, FRAME_TOP - BOTTOM_MARGIN,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="content",
    )
    doc.addPageTemplates([PageTemplate(id="fach", frames=[frame], onPage=make_footer(footer_center))])
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
    parser.add_argument(
        "--subjects", nargs="+", default=None, metavar="FACH",
        help="Nur diese Fächer aufnehmen (Default: alle vorhandenen Fächer)",
    )
    parser.add_argument(
        "--list-subjects", action="store_true",
        help="Nur die verfügbaren Fächer auflisten und beenden",
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

    if args.list_subjects:
        for subject in subjects:
            print(subject)
        return

    if args.subjects:
        by_casefold = {s.casefold(): s for s in subjects}
        selected: list[str] = []
        unknown: list[str] = []
        for wanted in args.subjects:
            match = by_casefold.get(wanted.casefold())
            if match is None:
                unknown.append(wanted)
            elif match not in selected:
                selected.append(match)
        if unknown:
            print(f"Fehler: Unbekannte Fächer für Schuljahr {schoolyear_id}: {', '.join(unknown)}", file=sys.stderr)
            print(f"Verfügbare Fächer: {', '.join(subjects)}", file=sys.stderr)
            sys.exit(1)
        subjects = sorted(selected, key=str.casefold)

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
        footer_center = f"{SCHOOL_NAME} – Bücherliste Fächer (Schuljahr {schoolyear_id})"
        write_pdf(out_path, story, title=f"Bücherliste Fächer {schoolyear_id}", footer_center=footer_center)
        print(f"PDF gespeichert: {out_path}")
    else:
        for subject in subjects:
            story = subject_story(subject, by_subject[subject], schoolyear_id)
            out_path = out_dir / f"Bücherliste {subject} {sy_label}.pdf"
            footer_center = f"{SCHOOL_NAME} – Bücherliste {subject} (Schuljahr {schoolyear_id})"
            write_pdf(out_path, story, title=f"Bücherliste {subject} {schoolyear_id}", footer_center=footer_center)
            print(f"PDF gespeichert: {out_path}")


if __name__ == "__main__":
    main()
