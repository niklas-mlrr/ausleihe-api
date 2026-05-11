"""
Schüler nach Name suchen.

Verwendung:
  python3 examples/students/search.py <nachname>
  python3 examples/students/search.py <nachname> <vorname>
  python3 examples/students/search.py --firstname <vorname>
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die

args = sys.argv[1:]
lastname = ""
firstname = ""

if not args:
    die("Verwendung: search.py <nachname> [vorname]  oder  search.py --firstname <vorname>")

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
