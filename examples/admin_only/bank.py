"""
Bankverbindungen abrufen. [Admin]

Verwendung:
  python3 -m examples.admin_only.bank
"""
import json

from examples._common import ForbiddenError, die, make_client

client = make_client()

try:
    bank = client.admin.get_bank()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(json.dumps(bank, indent=2, ensure_ascii=False))
