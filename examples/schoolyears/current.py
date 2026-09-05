"""
Aktuelles Schuljahr abrufen (GET /schoolyears/current). [Helfer]

Verwendung:
  python3 -m examples.schoolyears.current
"""
import json

from examples._common import make_client

client = make_client()
sy = client.schoolyears.get_current()

print(f"Aktuelles Schuljahr: {sy['id']} ({sy['name']})")
print(f"  Beginn:      {sy['begin'][:10]}")
print(f"  Ende:        {sy['end'][:10]}")
print(f"  Anmeldung:   {sy.get('enrollment_begin', '?')[:10]} – {sy.get('enrollment_end', '?')[:10]}")
print()
print(json.dumps(sy, indent=2, ensure_ascii=False))
