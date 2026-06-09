"""
Schüler-ID-Barcode-Zuordnung abrufen oder setzen. [Admin]

Verwendung:
  python3 examples/admin_only/studentids.py <code>                 # lesen (GET)
  AUSLEIHE_ALLOW_WRITES=1 python3 examples/admin_only/studentids.py <code> <student_id>  # SCHREIBEND

ACHTUNG: Das Setzen einer Zuordnung ist ein SCHREIBENDER Request gegen die
PRODUKTION. Standardmäßig blockiert; nur mit AUSLEIHE_ALLOW_WRITES=1 freigeschaltet.
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die("Verwendung: studentids.py <code> [student_id]")

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
