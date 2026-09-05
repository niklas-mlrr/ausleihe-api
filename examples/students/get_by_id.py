"""
Einzelnen Schüler nach ID abrufen.

Verwendung:
  python3 -m examples.students.get_by_id <id>
  python3 -m examples.students.get_by_id 2167
"""
import sys

from examples._common import NotFoundError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.students.get_by_id <id>")

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
