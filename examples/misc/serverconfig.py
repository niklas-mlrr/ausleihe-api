"""
Server-Konfiguration abrufen (GET /serverconfig). [Helfer, read-only]

Bootstrap-Config des Frontends: IServ-Lizenzstufe und Servername. Die Lizenz
steuert das Feature-Gating (z.B. schaltet "COMPLETE" das Anmelde-/Enrollment-
Feature frei).

Verwendung:
  python3 examples/misc/serverconfig.py
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client
import json

client = make_client()
config = client.get("/serverconfig")

license_ = config.get("license")
iserv = config.get("iserv", {})

print(f"Lizenz:       {license_}")
print(f"Hostname:     {iserv.get('hostname')}")
print(f"Servername:   {iserv.get('servername')}")
print(f"Enrollment-Feature: {'verfügbar' if license_ == 'COMPLETE' else 'nicht verfügbar'}")
print()
print("Vollständige Antwort:")
print(json.dumps(config, indent=2, ensure_ascii=False))
