"""
Schüler nach Name suchen.

Verwendung:
  # Nach Nachname (optional zusätzlich Vorname):
  python3 -m examples.students.search <nachname> [vorname]
  python3 -m examples.students.search Müller
  python3 -m examples.students.search Müller Anna

  # Nur nach Vorname:
  python3 -m examples.students.search --firstname <vorname>
  python3 -m examples.students.search --firstname Anna
"""
import sys

from examples._common import die, make_client

args = sys.argv[1:]
lastname = ""
firstname = ""

if not args:
    die("Verwendung: python3 -m examples.students.search <nachname> [vorname]"
        "  oder  python3 -m examples.students.search --firstname <vorname>")

if args[0] == "--firstname":
    firstname = args[1] if len(args) > 1 else die("--firstname benötigt einen Wert.")
else:
    lastname = args[0]
    if len(args) > 1:
        firstname = args[1]

client = make_client()
students = client.students.search_by_name(lastname=lastname, firstname=firstname)

if not students:
    print("Keine Schüler gefunden.")
    sys.exit(0)

print(f"{len(students)} Schüler gefunden:")
for s in students:
    dob = s.date_of_birth.strftime("%d.%m.%Y") if s.date_of_birth else "-"
    print(f"  ID {s.id:>5}  {s.firstname:<12} {s.lastname:<18} ({s.iserv_act})")
