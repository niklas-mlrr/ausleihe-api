"""
READ-ONLY: Alle Anmeldungen eines Schülers anhand seiner ID finden. [Admin]

Anmelde-Objekte enthalten keine Schüler-ID direkt, sondern Name + Geburtsdatum.
Dieses Skript holt den Schüler per ID, durchsucht dann die Anmeldungen aller
Schuljahre und matcht über firstname + lastname + date_of_birth.
Es werden ausschliesslich GET-Requests gemacht; KEINE Daten werden geaendert.

Verwendung:
  PYTHONPATH=. python3 examples/students/enrollments_by_id.py <student_id>
  PYTHONPATH=. python3 examples/students/enrollments_by_id.py 2167
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die("Verwendung: enrollments_by_id.py <student_id>")

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

matches = []
for yid in years:
    try:
        enr = client.admin.get_enrollments(yid)
    except (ForbiddenError, Exception):
        continue
    for e in enr:
        if (str(e.get("student_firstname", "")).strip().lower() == s.firstname.strip().lower()
                and str(e.get("student_lastname", "")).strip().lower() == s.lastname.strip().lower()
                and (dob is None or str(e.get("student_date_of_birth", ""))[:10] == dob)):
            e["_schoolyear"] = yid
            matches.append(e)

print(f"\nGefundene Anmeldungen: {len(matches)}\n")
for e in matches:
    items = e.get("booklistItems") or []
    pays = e.get("payments") or []
    print(f"=== Schuljahr {e.get('_schoolyear')} (enrollment id {e.get('id')}) ===")
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
    print(f"  Anzahl Buch-Items      : {len(items)}")
    if pays:
        print(f"  Zahlungen ({len(pays)}):")
        for p in pays:
            print(f"     - {json.dumps(p, ensure_ascii=False)}")
    print()
