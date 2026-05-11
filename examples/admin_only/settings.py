"""
Systemeinstellungen abrufen. [Admin]

Verwendung:
  python3 examples/admin_only/settings.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

client = make_client()

try:
    settings = client.admin.get_settings()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(json.dumps(settings, indent=2, ensure_ascii=False))
