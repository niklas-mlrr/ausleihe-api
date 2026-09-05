"""
Einzelnes Schuljahr mit Bücherlisten-Übersicht (GET /schoolyears/:id). [Helfer]

Verwendung:
  python3 -m examples.schoolyears.get_by_id <schoolyear_id>
  python3 -m examples.schoolyears.get_by_id "2025/2026"
"""
import json
import sys

from examples._common import die, make_client

if len(sys.argv) < 2:
    die('Verwendung: python3 -m examples.schoolyears.get_by_id <schoolyear_id>  (z.B. "2025/2026")')

client = make_client()
sy = client.schoolyears.get_by_id(sys.argv[1])

print(f"Schuljahr: {sy['id']} ({sy['name']})")
booklists = sy.get("Booklists", [])
print(f"Bücherlisten ({len(booklists)}):")
for bl in booklists:
    print(f"  [{bl['id']}] {bl.get('name', bl.get('title', '?'))}")
print()
print(json.dumps(sy, indent=2, ensure_ascii=False))
