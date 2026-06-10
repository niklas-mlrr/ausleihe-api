"""
READ-ONLY: Aktuell ausgeliehene Bücher eines Schülers, gefiltert nach Schuljahr. [Helfer]

Die API kennt nur die *aktuell* ausgeliehenen Bücher (GET /students/:id/books) —
ein Buch trägt kein Schuljahr-Feld, sondern nur ein Ausgabedatum (distributed_at).
Bücher werden im Sommer VOR dem offiziellen Schuljahresbeginn ausgegeben, daher
ist das Fenster eines Schuljahrs:  [ Ende des Vorjahres ... Ende dieses Jahres ].
Ein aktuell geliehenes Buch zählt zum Schuljahr, wenn sein distributed_at in
dieses Fenster fällt.

Ohne Angabe wird das aktuelle Schuljahr verwendet. Es werden ausschliesslich
GET-Requests gemacht; KEINE Daten werden geaendert.

Verwendung:
  python3 examples/students/borrowed_books_by_year.py <student_id> [schuljahr]
  python3 examples/students/borrowed_books_by_year.py 2167             # aktuelles Jahr
  python3 examples/students/borrowed_books_by_year.py 2167 2025/2026    # bestimmtes Jahr
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, NotFoundError, die
from datetime import datetime, timezone

if len(sys.argv) < 2:
    die("Verwendung: borrowed_books_by_year.py <student_id> [schuljahr]")

try:
    sid = int(sys.argv[1])
except ValueError:
    die("student_id muss eine Zahl sein.")

arg_year = sys.argv[2] if len(sys.argv) > 2 else None
client = make_client()


def parse_iso(value):
    """ISO-Datum der API ('...Z') -> timezone-aware datetime, sonst None."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def prev_year_id(sy_id):
    """'2025/2026' -> '2024/2025'."""
    try:
        a, b = sy_id.split("/")
        return f"{int(a) - 1}/{int(b) - 1}"
    except Exception:
        return None


# 1. Schüler holen (GET, read-only)
try:
    student = client.students.get_by_id(sid)
except NotFoundError:
    die(f"Kein Schüler mit ID {sid} gefunden.")
print(f"Schüler {sid}: {student.firstname} {student.lastname}  act={student.iserv_act}")

# 2. Ziel-Schuljahr bestimmen (GET, read-only)
if arg_year:
    try:
        year = client.schoolyears.get_by_id(arg_year)
    except NotFoundError:
        die(f"Schuljahr {arg_year!r} nicht gefunden. Format: YYYY/YYYY, z. B. 2025/2026.")
else:
    year = client.schoolyears.get_current()

sy_id = year.get("id")
upper = parse_iso(year.get("end"))

# Untergrenze = Ende des Vorjahres (Ausgabe startet danach); Fallback: begin dieses Jahres
lower = None
prev_id = prev_year_id(sy_id)
if prev_id:
    try:
        lower = parse_iso(client.schoolyears.get_by_id(prev_id).get("end"))
    except NotFoundError:
        lower = None
if lower is None:
    lower = parse_iso(year.get("begin"))

print(f"\nSchuljahr: {sy_id}")
print(f"  Zeitfenster Ausgabe: {lower:%d.%m.%Y} – {upper:%d.%m.%Y}" if lower and upper
      else f"  Zeitfenster Ausgabe: {lower} – {upper}")

# 3. Aktuell ausgeliehene Bücher holen und nach Ausgabedatum ins Fenster filtern
books = client.students.get_books(sid)


def in_window(b):
    d = b.distributed_at
    if d is None:
        return False
    if lower and d < lower:
        return False
    if upper and d > upper:
        return False
    return True


matched = [b for b in books if in_window(b)]
no_date = [b for b in books if b.distributed_at is None]

print(f"\nAktuell ausgeliehen gesamt: {len(books)}")
print(f"Davon im Schuljahr {sy_id}: {len(matched)}\n")

total_fee = 0.0
for b in sorted(matched, key=lambda x: x.distributed_at):
    title = b.series.title if b.series else b.isbn
    publisher = b.series.publisher if b.series else "-"
    fee = b.series.fee if b.series and b.series.fee is not None else 0.0
    total_fee += fee
    since = b.distributed_at.strftime("%d.%m.%Y") if b.distributed_at else "unbekannt"
    print(f"  [{b.code}] {title}")
    print(f"           Verlag: {publisher} | ISBN: {b.isbn} | seit: {since} | Gebühr: {fee}")

if matched:
    print(f"\nSumme Leihgebühr (laut Serie): {total_fee:.2f} EUR")
if no_date:
    print(f"\nHinweis: {len(no_date)} ausgeliehene(s) Buch/Bücher ohne distributed_at "
          f"(keinem Schuljahr zuordenbar).")
