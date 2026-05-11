"""
Ausleihregeln abrufen (öffentlicher Endpunkt, kein Auth nötig).

Verwendung:
  python3 examples/misc/borrowing_rules.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client
import re

client = make_client()
rules = client.get_borrowing_rules()

print(f"{len(rules)} Ausleihregeln:\n")
for r in rules:
    created = ""
    if r.get("created_at"):
        created = f"  (erstellt: {r['created_at'][:10]})"
    # HTML-Tags aus dem Text entfernen für lesbare Ausgabe
    text = re.sub(r"<[^>]+>", "", r.get("text", "")).strip()
    print(f"--- Regel {r.get('id')} ---{created}")
    print(text[:300])
    print()
