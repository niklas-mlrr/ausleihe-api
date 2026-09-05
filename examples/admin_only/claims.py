"""
Alle Forderungen abrufen, oder Mahnbriefe als PDF. [Admin]

Verwendung:
  # Forderungen auflisten (erste 10):
  python3 -m examples.admin_only.claims

  # Mahnbriefe als PDF speichern (Dateiname optional, Standard: mahnbriefe.pdf):
  python3 -m examples.admin_only.claims pdf [ausgabe.pdf]
  python3 -m examples.admin_only.claims pdf mahnbriefe.pdf
"""
import json
import sys

from examples._common import ForbiddenError, die, make_client

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
