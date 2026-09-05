"""
Schuljahre abrufen. [Admin]

Verwendung:
  python3 -m examples.admin_only.schoolyears
"""
import json

from examples._common import ForbiddenError, die, make_client

client = make_client()

try:
    years = client.admin.get_schoolyears()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(years)} Schuljahr(e):")
for y in years:
    print(f"  {json.dumps(y, ensure_ascii=False)}")
