"""
Leihschein als PDF herunterladen.

Verwendung:
  python3 examples/misc/loan_slip_pdf.py <student_id>
  python3 examples/misc/loan_slip_pdf.py <student_id> <ausgabe.pdf>
  python3 examples/misc/loan_slip_pdf.py 2167 leihschein.pdf
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die

if len(sys.argv) < 2:
    die("Verwendung: loan_slip_pdf.py <student_id> [ausgabe.pdf]")

student_id = int(sys.argv[1])
outfile = sys.argv[2] if len(sys.argv) >= 3 else f"leihschein_{student_id}.pdf"

client = make_client()
pdf = client.get_loan_slip_pdf(student_id)

with open(outfile, "wb") as f:
    f.write(pdf)

print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")
