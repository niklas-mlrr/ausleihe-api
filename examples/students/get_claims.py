"""
Forderungen (Mahnungen/Schadensersatz) eines Schülers abrufen.
Erfordert mod_sbl_grant_always_enrollments oder Verwalter-Rolle.

Verwendung:
  python3 examples/students/get_claims.py <id>
  python3 examples/students/get_claims.py 2167
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die("Verwendung: get_claims.py <id>")

student_id = int(sys.argv[1])
client = make_client()

try:
    claims = client.students.get_claims(student_id)
except ForbiddenError:
    die("Kein Zugriff. Benötigt: mod_sbl_grant_always_enrollments oder Verwalter-Rolle.")

if not claims:
    print(f"Keine Forderungen für Schüler {student_id}.")
else:
    # Claim ist ein rohes dict (kein Dataclass-Modell) — siehe schemas.md.
    print(f"{len(claims)} Forderung(en) für Schüler {student_id}:")
    print(json.dumps(claims, indent=2, ensure_ascii=False))
