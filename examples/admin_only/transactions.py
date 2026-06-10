"""
Banktransaktionen abrufen. [Admin, read-only]

Echter Endpunkt: GET /bank/transactions/ (liefert JSON). Serverseitige Filter:

Verwendung:
  python3 examples/admin_only/transactions.py             # alle (erste 10)
  python3 examples/admin_only/transactions.py open        # Zuordnung offen (dedicated=false)
  python3 examples/admin_only/transactions.py assigned    # vollständig zugeordnet (dedicated=true)
  python3 examples/admin_only/transactions.py ignored     # ausgeblendet (ignored=true)
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

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
