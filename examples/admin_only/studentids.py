"""
Schüler-ID-Barcode-Zuordnung abrufen oder setzen. [Admin]

Verwendung:
  python3 examples/admin_only/studentids.py <code>
  python3 examples/admin_only/studentids.py <code> <student_id>
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die("Verwendung: studentids.py <code> [student_id]")

client = make_client()
code = sys.argv[1]

try:
    if len(sys.argv) >= 3:
        result = client.admin.set_student_id(code, int(sys.argv[2]))
        print(f"Gesetzt: {json.dumps(result, ensure_ascii=False)}")
    else:
        result = client.admin.get_student_id(code)
        print(json.dumps(result, indent=2, ensure_ascii=False))
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")
