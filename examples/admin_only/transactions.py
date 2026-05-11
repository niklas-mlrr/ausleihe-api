"""
Zahlungstransaktionen abrufen. [Admin]

Verwendung:
  python3 examples/admin_only/transactions.py
  python3 examples/admin_only/transactions.py csv
  python3 examples/admin_only/transactions.py xlsx
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

client = make_client()
fmt = sys.argv[1] if len(sys.argv) >= 2 else None

try:
    transactions = client.admin.get_transactions(format=fmt)
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

if isinstance(transactions, list):
    print(f"{len(transactions)} Transaktion(en):")
    for t in transactions[:10]:
        print(f"  {json.dumps(t, ensure_ascii=False)}")
    if len(transactions) > 10:
        print(f"  ... und {len(transactions) - 10} weitere.")
else:
    print(transactions)
