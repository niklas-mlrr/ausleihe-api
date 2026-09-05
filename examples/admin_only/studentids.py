"""
Schüler-ID-Barcode-Zuordnung abrufen oder setzen. [Admin]

Verwendung:
  # Zuordnung lesen (GET):
  python3 -m examples.admin_only.studentids <code>
  python3 -m examples.admin_only.studentids 00015193

  # Zuordnung setzen (SCHREIBEND, nur mit Freigabe):
  AUSLEIHE_ALLOW_WRITES=1 python3 -m examples.admin_only.studentids <code> <student_id>
  AUSLEIHE_ALLOW_WRITES=1 python3 -m examples.admin_only.studentids 00015193 2167

ACHTUNG: Das Setzen einer Zuordnung ist ein SCHREIBENDER Request gegen die
PRODUKTION. Standardmäßig blockiert; nur mit AUSLEIHE_ALLOW_WRITES=1 freigeschaltet.
"""
import json
import os
import sys

from examples._common import ForbiddenError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.admin_only.studentids <code> [student_id]")

code = sys.argv[1]
want_write = len(sys.argv) >= 3

if want_write and os.environ.get("AUSLEIHE_ALLOW_WRITES") != "1":
    die("Schreibzugriff blockiert. Mit AUSLEIHE_ALLOW_WRITES=1 erneut ausführen "
        "(wirkt auf die PRODUKTION!).")

client = make_client(allow_writes=want_write)

try:
    if want_write:
        result = client.admin.set_student_id(code, int(sys.argv[2]))
        print(f"Gesetzt: {json.dumps(result, ensure_ascii=False)}")
    else:
        result = client.admin.get_student_id(code)
        print(json.dumps(result, indent=2, ensure_ascii=False))
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")
