"""
Ausleihregeln abrufen (öffentlicher Endpunkt, kein Auth nötig).

Verwendung:
  python3 -m examples.misc.borrowing_rules
"""
import re

from examples._common import make_client

client = make_client()
rules = client.get_borrowing_rules()

print(f"{len(rules)} Ausleihregeln:\n")
for r in rules:
    created = f"  (erstellt: {r.created_at.date()})" if r.created_at else ""
    # HTML-Tags aus dem Text entfernen für lesbare Ausgabe
    text = re.sub(r"<[^>]+>", "", r.text).strip()
    print(f"--- Regel {r.id} ---{created}")
    print(text[:300])
    print()
