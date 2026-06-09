"""
Einzelnes Schuljahr mit Bücherlisten-Übersicht (GET /schoolyears/:id). [Helfer]

Verwendung:
  python3 examples/schoolyears/get_by_id.py <schoolyear_id>
  python3 examples/schoolyears/get_by_id.py "2025/2026"
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die
import json

if len(sys.argv) < 2:
    die('Verwendung: get_by_id.py <schoolyear_id>  (z.B. "2025/2026")')

client = make_client()
sy = client.schoolyears.get_by_id(sys.argv[1])

print(f"Schuljahr: {sy['id']} ({sy['name']})")
booklists = sy.get("Booklists", [])
print(f"Bücherlisten ({len(booklists)}):")
for bl in booklists:
    print(f"  [{bl['id']}] {bl.get('name', bl.get('title', '?'))}")
print()
print(json.dumps(sy, indent=2, ensure_ascii=False))
