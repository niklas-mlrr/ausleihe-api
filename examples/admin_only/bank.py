"""
Bankverbindungen abrufen. [Admin]

Verwendung:
  python3 examples/admin_only/bank.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

client = make_client()

try:
    bank = client.admin.get_bank()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(json.dumps(bank, indent=2, ensure_ascii=False))
