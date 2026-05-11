"""
Schuljahre abrufen. [Admin]

Verwendung:
  python3 examples/admin_only/schoolyears.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

client = make_client()

try:
    years = client.admin.get_schoolyears()
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(years)} Schuljahr(e):")
for y in years:
    print(f"  {json.dumps(y, ensure_ascii=False)}")
