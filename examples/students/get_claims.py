"""
Forderungen (Mahnungen/Schadensersatz) eines Schülers abrufen.
Erfordert mod_sbl_grant_always_enrollments oder Verwalter-Rolle.

Verwendung:
  python3 -m examples.students.get_claims <id>
  python3 -m examples.students.get_claims 2167
"""
import json
import sys

from examples._common import ForbiddenError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.students.get_claims <id>")

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
