"""
Anmeldungen eines Schuljahrs abrufen, oder als PDF exportieren. [Admin]

Verwendung:
  # Anmeldungen eines Schuljahrs auflisten:
  python3 examples/admin_only/enrollments.py <schoolyear_id>
  python3 examples/admin_only/enrollments.py "2025/2026"

  # Befreiungen als PDF exportieren (Dateiname optional):
  python3 examples/admin_only/enrollments.py <schoolyear_id> exemptions [ausgabe.pdf]
  python3 examples/admin_only/enrollments.py "2025/2026" exemptions

  # Klassenlisten als PDF exportieren (Dateiname optional):
  python3 examples/admin_only/enrollments.py <schoolyear_id> forms [ausgabe.pdf]
  python3 examples/admin_only/enrollments.py "2025/2026" forms

schoolyear_id: Schuljahr im Format "YYYY/YYYY" (z.B. "2025/2026").
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die('Verwendung: enrollments.py <schoolyear_id> [exemptions|forms] [ausgabe.pdf]')

client = make_client()
sy_id = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) >= 3 else None
safe_sy = sy_id.replace("/", "_")

try:
    if mode == "exemptions":
        outfile = sys.argv[3] if len(sys.argv) >= 4 else f"befreiungen_{safe_sy}.pdf"
        pdf = client.admin.get_enrollments_export_pdf(sy_id)
        with open(outfile, "wb") as f:
            f.write(pdf)
        print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")

    elif mode == "forms":
        outfile = sys.argv[3] if len(sys.argv) >= 4 else f"klassenlisten_{safe_sy}.pdf"
        pdf = client.admin.get_form_students_pdf(sy_id)
        with open(outfile, "wb") as f:
            f.write(pdf)
        print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")

    else:
        enrollments = client.admin.get_enrollments(sy_id)
        print(f"{len(enrollments)} Anmeldung(en) für Schuljahr {sy_id}:")
        for e in enrollments[:10]:
            print(f"  {json.dumps(e, ensure_ascii=False)}")
        if len(enrollments) > 10:
            print(f"  ... und {len(enrollments) - 10} weitere.")

except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")
