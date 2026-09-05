"""
READ-ONLY: Anmeldung eines Schülers für ein Schuljahr anzeigen. [Admin]

Fokussierte Variante von enrollments_by_id.py: statt alle Schuljahre zu
durchsuchen, wird nur ein einzelnes Schuljahr betrachtet. Ohne Angabe wird das
aktuelle Schuljahr (schoolyears/current) verwendet.

Anmelde-Objekte enthalten keine Schüler-ID direkt, sondern Name + Geburtsdatum
(siehe Wiki: Data Schemas). Daher: Schüler per ID holen, dann die Anmeldungen
des Schuljahrs über firstname + lastname + date_of_birth matchen.
Angemeldete Bücher (booklistItems) werden über die ISBN zu Titel/Verlag aufgelöst.

Es werden ausschliesslich GET-Requests gemacht; KEINE Daten werden angelegt
oder geaendert (Anmeldungen ANLEGEN waere POST/PUT -> gegen Produktion tabu).

Verwendung:
  python3 -m examples.students.enrollment_current_year_by_id <student_id> [schuljahr]
  python3 -m examples.students.enrollment_current_year_by_id 2167             # aktuelles Jahr
  python3 -m examples.students.enrollment_current_year_by_id 2167 2024/2025    # bestimmtes Jahr
"""
import sys

from examples._common import ForbiddenError, NotFoundError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.students.enrollment_current_year_by_id <student_id> [schuljahr]")

try:
    sid = int(sys.argv[1])
except ValueError:
    die("student_id muss eine Zahl sein.")

# Optionales Schuljahr-Argument (String wie "2025/2026"); sonst aktuelles Jahr.
arg_year = sys.argv[2] if len(sys.argv) > 2 else None

client = make_client()

# 1. Schüler holen (GET, read-only)
s = client.students.get_by_id(sid)
dob = str(s.date_of_birth)[:10] if s.date_of_birth else None
print(f"Schüler {sid}: {s.firstname} {s.lastname}  geb. {dob}  act={s.iserv_act}")

# 2. Schuljahr bestimmen (GET, read-only)
if arg_year:
    try:
        year = client.schoolyears.get_by_id(arg_year)
    except NotFoundError:
        die(f"Schuljahr {arg_year!r} nicht gefunden. Format: YYYY/YYYY, z. B. 2025/2026.")
    label = "Gewähltes Schuljahr"
else:
    year = client.schoolyears.get_current()
    label = "Aktuelles Schuljahr"

cur_id = year.get("id")
print(f"\n{label}: {cur_id}")
print(f"  enrollment_enabled={year.get('enrollment_enabled')} "
      f"enrollment_begin={year.get('enrollment_begin')} "
      f"enrollment_end={year.get('enrollment_end')}")

# 3. Anmeldungen des aktuellen Schuljahrs laden und auf den Schüler matchen
try:
    enrollments = client.admin.get_enrollments(cur_id)
except ForbiddenError:
    die("Kein Zugriff auf /schoolyears/.../enrollments (403). Verwalter-Rolle benötigt.")


def matches_student(e: dict) -> bool:
    same_first = str(e.get("student_firstname", "")).strip().lower() == s.firstname.strip().lower()
    same_last = str(e.get("student_lastname", "")).strip().lower() == s.lastname.strip().lower()
    same_dob = dob is None or str(e.get("student_date_of_birth", ""))[:10] == dob
    return same_first and same_last and same_dob


matches = [e for e in enrollments if matches_student(e)]

print(f"\nAnmeldungen im Schuljahr {cur_id}: {len(matches)}")
if not matches:
    print("  -> Keine Anmeldung für diesen Schüler im aktuellen Schuljahr gefunden.")
    sys.exit(0)


def series_label(isbn: str) -> str:
    """ISBN -> 'Titel (Verlag)'. Bei Fehler nur die ISBN zurückgeben."""
    try:
        ser = client.series.get_by_isbn(isbn)
        return f"{ser.title} ({ser.publisher})"
    except Exception:
        return isbn


for e in matches:
    items = e.get("booklistItems") or []
    pays = e.get("payments") or []
    print(f"\n=== enrollment id {e.get('id')} ===")
    print(f"  Jahrgangsstufe geplant : {e.get('student_upcoming_grade')} / {e.get('student_upcoming_form')}")
    print(f"  Gebühr fee/feeFull     : {e.get('fee')} / {e.get('feeFull')}")
    print(f"  bezahlt / offen        : {e.get('amountPaid')} / {e.get('amountOpen')}")
    print(f"  Ermäßigung             : request={e.get('remission_request')} accepted={e.get('remission_accepted')}")
    print(f"  Befreiung              : request={e.get('exemption_request')} accepted={e.get('exemption_accepted')}")
    print(f"  needsHandsOn           : {e.get('needsHandsOn')}")
    print(f"  payment_ref            : {e.get('payment_ref')}")
    print(f"  zugewiesen             : at={e.get('assigned_at')} by={e.get('assigned_by')} to={e.get('assigned_to')}")
    print(f"  created / deleted      : {e.get('created_at')} / del={e.get('deleted_at')}")
    print(f"  Kontakt (legal)        : {e.get('legal_firstname')} {e.get('legal_lastname')}, "
          f"{e.get('legal_street')} {e.get('legal_nr')}, {e.get('legal_zip')} {e.get('legal_city')}, "
          f"{e.get('legal_phone')} {e.get('legal_mail')}")
    print(f"  Angemeldete Bücher ({len(items)}):")
    for it in items:
        isbn = it.get("series")
        ebi = it.get("EnrollmentBooklistItem") or {}
        fee = ebi.get("fee")
        borrowable = it.get("borrowable")  # liegt auf Item-Ebene, nicht in EnrollmentBooklistItem
        print(f"     - {series_label(isbn)}  [ISBN {isbn}]  Gebühr={fee}  ausleihbar={borrowable}")
    if pays:
        print(f"  Zahlungen ({len(pays)}):")
        for p in pays:
            print(f"     - betrag={p.get('amount')} datum={p.get('date') or p.get('created_at')} "
                  f"ref={p.get('payment_ref')}")
