"""
Aktuelles Schuljahr abrufen (GET /schoolyears/current). [Helfer]

Verwendung:
  python3 examples/schoolyears/current.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client
import json

client = make_client()
sy = client.schoolyears.get_current()

print(f"Aktuelles Schuljahr: {sy['id']} ({sy['name']})")
print(f"  Beginn:      {sy['begin'][:10]}")
print(f"  Ende:        {sy['end'][:10]}")
print(f"  Anmeldung:   {sy.get('enrollment_begin', '?')[:10]} – {sy.get('enrollment_end', '?')[:10]}")
print()
print(json.dumps(sy, indent=2, ensure_ascii=False))
