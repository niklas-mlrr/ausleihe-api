"""
Systemeinstellungen abrufen. [Admin]

Verwendung:
  python3 -m examples.admin_only.settings
"""
import json

from examples._common import ForbiddenError, die, make_client

client = make_client()

try:
    settings = client.admin.get_settings()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(json.dumps(settings, indent=2, ensure_ascii=False))
