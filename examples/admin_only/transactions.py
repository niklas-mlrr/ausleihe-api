"""
Banktransaktionen abrufen. [Admin, read-only]

Echter Endpunkt: GET /bank/transactions/ (liefert JSON). Serverseitige Filter:

Verwendung:
  python3 -m examples.admin_only.transactions             # alle (erste 10)
  python3 -m examples.admin_only.transactions open        # Zuordnung offen (dedicated=false)
  python3 -m examples.admin_only.transactions assigned    # vollständig zugeordnet (dedicated=true)
  python3 -m examples.admin_only.transactions ignored     # ausgeblendet (ignored=true)
"""
import json
import sys

from examples._common import ForbiddenError, die, make_client

client = make_client()
mode = sys.argv[1] if len(sys.argv) >= 2 else None

kwargs = {}
if mode == "open":
    kwargs = {"dedicated": False}
elif mode == "assigned":
    kwargs = {"dedicated": True}
elif mode == "ignored":
    kwargs = {"ignored": True}
elif mode:
    die('Unbekannter Filter. Erlaubt: open | assigned | ignored (oder ohne Argument).')

try:
    transactions = client.admin.get_transactions(**kwargs)
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(transactions)} Transaktion(en){' (' + mode + ')' if mode else ''}:")
for t in transactions[:10]:
    print(f"  {json.dumps(t, ensure_ascii=False)}")
if len(transactions) > 10:
    print(f"  ... und {len(transactions) - 10} weitere.")
