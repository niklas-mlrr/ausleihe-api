"""
READ-ONLY: Angemeldete Bücher (ISBNs) eines Schülers pro Schuljahr auflisten. [Admin]

Anmelde-Objekte enthalten keine Schüler-ID direkt, sondern Name + Geburtsdatum.
Dieses Skript holt den Schüler per ID, durchsucht die Anmeldungen aller Schuljahre
und matcht über firstname + lastname + date_of_birth. Pro gefundener Anmeldung
werden die angemeldeten Bücher ausgegeben:

  ISBN  = booklistItem["series"]
  Gebühr = booklistItem["EnrollmentBooklistItem"]["fee"]
  ausleihbar = booklistItem["borrowable"]

Titel/Verlag werden über client.series aufgelöst (einmalig gecacht).
Es werden ausschliesslich GET-Requests gemacht; KEINE Daten werden geaendert.

Verwendung:
  python3 -m examples.students.enrolled_books_by_id <student_id>
  python3 -m examples.students.enrolled_books_by_id 2167
"""
import sys

from examples._common import ForbiddenError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.students.enrolled_books_by_id <student_id>")

try:
    sid = int(sys.argv[1])
except ValueError:
    die("student_id muss eine Zahl sein.")

client = make_client()

s = client.students.get_by_id(sid)
dob = str(s.date_of_birth)[:10] if s.date_of_birth else None
print(f"Schüler {sid}: {s.firstname} {s.lastname}  geb. {dob}  act={s.iserv_act}")

try:
    years = [y.get("id") for y in client.admin.get_schoolyears()]
except ForbiddenError:
    die("Kein Zugriff auf /schoolyears (403). Verwalter-Rolle benötigt.")

# Serien-Lookup einmalig holen (ISBN -> Series), zur Titel-/Verlagsauflösung
series_by_isbn = {ser.isbn: ser for ser in client.series.get_all()}


def matches_student(e: dict) -> bool:
    return (
        str(e.get("student_firstname", "")).strip().lower() == s.firstname.strip().lower()
        and str(e.get("student_lastname", "")).strip().lower() == s.lastname.strip().lower()
        and (dob is None or str(e.get("student_date_of_birth", ""))[:10] == dob)
    )


found = 0
for yid in years:
    try:
        enrollments = client.admin.get_enrollments(yid)
    except (ForbiddenError, Exception):
        continue
    for e in enrollments:
        if not matches_student(e):
            continue
        found += 1
        items = e.get("booklistItems") or []
        total = e.get("fee")
        print(f"\n=== Schuljahr {yid} (enrollment id {e.get('id')}) — {len(items)} Buch/Bücher, Gebühr {total} EUR ===")
        for it in items:
            isbn = it.get("series")
            fee = (it.get("EnrollmentBooklistItem") or {}).get("fee")
            borrowable = it.get("borrowable")
            ser = series_by_isbn.get(isbn)
            title = f"{ser.title} ({ser.publisher})" if ser else "?"
            fee_str = f"{fee:>6} EUR" if fee is not None else "    — EUR"
            print(f"  {isbn}  {fee_str}  borrowable={borrowable}  {title}")

if not found:
    print("\nKeine Anmeldungen gefunden.")
