"""
Alle Forderungen abrufen, oder Mahnbriefe als PDF. [Admin]

Verwendung:
  python3 examples/admin_only/claims.py
  python3 examples/admin_only/claims.py pdf [ausgabe.pdf]
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

client = make_client()
mode = sys.argv[1] if len(sys.argv) >= 2 else None

try:
    if mode == "pdf":
        outfile = sys.argv[2] if len(sys.argv) >= 3 else "mahnbriefe.pdf"
        pdf = client.admin.get_claim_letters_pdf()
        with open(outfile, "wb") as f:
            f.write(pdf)
        print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")
    else:
        claims = client.admin.get_claims()
        print(f"{len(claims)} Forderung(en):")
        for c in claims[:10]:
            print(f"  {json.dumps(c, ensure_ascii=False)}")
        if len(claims) > 10:
            print(f"  ... und {len(claims) - 10} weitere.")

except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")
