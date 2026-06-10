"""
Leihschein als PDF herunterladen.

Verwendung:
  python3 examples/misc/loan_slip_pdf.py <student_id> [ausgabe.pdf] [--double]
  python3 examples/misc/loan_slip_pdf.py 2167
  python3 examples/misc/loan_slip_pdf.py 2167 leihschein.pdf
  python3 examples/misc/loan_slip_pdf.py 2167 --double

Ohne Dateiname wird "leihschein_<student_id>.pdf" verwendet.
Mit --double wird die zweiseitige Variante geladen (wie der Webseiten-Download:
Seite 1 = Schüler-Beleg, Seite 2 = Schul-Beleg mit abweichendem Signaturfeld).
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die

# Die Zweiseitigkeit steuert die "variant" (Schüler- + Schul-Beleg), nicht der
# vom Server ignorierte doublepage-Parameter.
double = "--double" in sys.argv
args = [a for a in sys.argv[1:] if a != "--double"]

if not args:
    die("Verwendung: loan_slip_pdf.py <student_id> [ausgabe.pdf] [--double]")

student_id = int(args[0])
outfile = args[1] if len(args) >= 2 else f"leihschein_{student_id}.pdf"
variant = "student-always_school-auto" if double else "student"

client = make_client()
pdf = client.get_loan_slip_pdf(student_id, variant=variant)

with open(outfile, "wb") as f:
    f.write(pdf)

print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")
