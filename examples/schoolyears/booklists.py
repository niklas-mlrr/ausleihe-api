"""
Bücherlisten eines Schuljahrs (GET /schoolyears/:id/booklists/). [Helfer]

Verwendung:
  python3 examples/schoolyears/booklists.py <schoolyear_id>
  python3 examples/schoolyears/booklists.py current
  python3 examples/schoolyears/booklists.py current
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die
import json

if len(sys.argv) < 2:
    die('Verwendung: booklists.py <schoolyear_id>  (z.B. "2025/2026" oder "current")')

client = make_client()
sy_id = sys.argv[1]

if sy_id == "current":
    sy_id = client.schoolyears.get_current()["id"]

lists = client.schoolyears.get_booklists(sy_id)
print(f"{len(lists)} Bücherliste(n) für Schuljahr {sy_id}:")
for bl in lists:
    bank = bl.get("BankAccount", {}) or {}
    print(f"  [{bl['id']}] {bl.get('name', bl.get('title', '?'))}  IBAN: {bank.get('iban', '?')}")
print()
print(json.dumps(lists, indent=2, ensure_ascii=False))
