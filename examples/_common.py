"""Gemeinsames Setup für alle Beispiel-Skripte."""
from __future__ import annotations

import os
import sys

# Das ist der EINZIGE verbliebene sys.path-Eingriff in examples/. Die
# Beispiel-Skripte selbst sind ein normales Paket (examples.<modul>) und
# brauchen ihn nicht mehr — der hier bleibt, weil der dokumentierte
# Nachfolgepfad "klonen, nicht installieren" ist: ohne editable install von
# `ausleihe-api` findet Python das Paket `ausleihe` sonst nicht, egal von wo
# `python3 -m examples....` aufgerufen wird.
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv

load_dotenv(os.path.join(_root, ".env"))

from ausleihe import AusleiheClient, AusleiheError, AuthError, ForbiddenError, NotFoundError


def make_client(allow_writes: bool = False) -> AusleiheClient:
    # Standardmäßig read-only — diese API zeigt auf die Produktion.
    return AusleiheClient(allow_writes=allow_writes)


def die(msg: str) -> None:
    print(f"Fehler: {msg}", file=sys.stderr)
    sys.exit(1)
