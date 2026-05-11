"""
Einzelnen Schüler nach ID abrufen.

Verwendung:
  python3 examples/students/get_by_id.py <id>
  python3 examples/students/get_by_id.py 2167
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, NotFoundError, die

if len(sys.argv) < 2:
    die("Verwendung: get_by_id.py <id>")

client = make_client()

try:
    s = client.students.get_by_id(int(sys.argv[1]))
except NotFoundError:
    die(f"Kein Schüler mit ID {sys.argv[1]} gefunden.")

dob = s.date_of_birth.strftime("%d.%m.%Y") if s.date_of_birth else "-"
left = s.left.strftime("%d.%m.%Y") if s.left else "-"
anon = s.anonymized_at.strftime("%d.%m.%Y") if s.anonymized_at else "-"

print(f"ID:            {s.id}")
print(f"Name:          {s.firstname} {s.lastname}")
print(f"IServ-Account: {s.iserv_act}")
print(f"Geburtsdatum:  {dob}")
print(f"Austritt:      {left}")
print(f"Anonymisiert:  {anon}")
print(f"Import-ID:     {s.import_id or '-'}")
