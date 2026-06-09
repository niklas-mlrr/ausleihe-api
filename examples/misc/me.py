"""
Eigenes Schüler-Profil abrufen (GET /me). [Helfer]

Verwendung:
  python3 examples/misc/me.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client
import json

client = make_client()
me = client.students.get_me()

print(f"Eingeloggt als: {me['firstname']} {me['lastname']} ({me['iserv_act']})")
print(f"Ausgeliehen:    {len(me.get('books', []))} Buch/Bücher")
print(f"Anmeldungen:    {len(me.get('enrollments', []))}")
print(f"Forderungen:    {len(me.get('claims', []))}")
print()
print("Vollständige Antwort:")
print(json.dumps(me, indent=2, ensure_ascii=False))
