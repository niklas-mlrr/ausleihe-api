"""
Bücherlisten eines Schuljahrs (GET /schoolyears/:id/booklists/). [Helfer]

Verwendung:
  python3 -m examples.schoolyears.booklists <schoolyear_id>
  python3 -m examples.schoolyears.booklists "2025/2026"
  python3 -m examples.schoolyears.booklists current   # laufendes Schuljahr

schoolyear_id: Schuljahr im Format "YYYY/YYYY", oder "current" für das laufende.
"""
import json
import sys

from examples._common import die, make_client

if len(sys.argv) < 2:
    die('Verwendung: python3 -m examples.schoolyears.booklists <schoolyear_id>'
        '  (z.B. "2025/2026" oder "current")')

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
