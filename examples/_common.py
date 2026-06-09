"""Gemeinsames Setup für alle Beispiel-Skripte."""
from __future__ import annotations

import os
import sys

# Projektroot zum Suchpfad hinzufügen, egal von wo das Skript aufgerufen wird
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

from ausleihe import AusleiheClient
from ausleihe import AusleiheError, AuthError, ForbiddenError, NotFoundError


def make_client(allow_writes: bool = False) -> AusleiheClient:
    # Standardmäßig read-only — diese API zeigt auf die Produktion.
    return AusleiheClient(allow_writes=allow_writes)


def die(msg: str) -> None:
    print(f"Fehler: {msg}", file=sys.stderr)
    sys.exit(1)
