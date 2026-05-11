"""
Alle Schüler abrufen.

Verwendung:
  python3 examples/students/get_all.py
  python3 examples/students/get_all.py --deleted
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client

include_deleted = "--deleted" in sys.argv

client = make_client()
students = client.students.get_all(include_deleted=include_deleted)

print(f"Schüler gesamt: {len(students)}")
print()
print("Erste 10 Einträge:")
for s in students[:10]:
    dob = s.date_of_birth.strftime("%d.%m.%Y") if s.date_of_birth else "-"
    print(f"  ID {s.id:>5}  {s.firstname:<12} {s.lastname:<18} ({s.iserv_act})  geb. {dob}")
