"""
Bücherlisten eines Schuljahrs abrufen, optional als PDF. [Admin]

Verwendung:
  python3 examples/admin_only/booklists.py <schoolyear_id>
  python3 examples/admin_only/booklists.py <schoolyear_id> <booklist_id> [ausgabe.pdf]
  python3 examples/admin_only/booklists.py "2025/2026"
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die
import json

if len(sys.argv) < 2:
    die('Verwendung: booklists.py <schoolyear_id> [booklist_id] [ausgabe.pdf]')

client = make_client()
sy_id = sys.argv[1]

try:
    if len(sys.argv) >= 3:
        # PDF einer einzelnen Bücherliste
        bl_id = int(sys.argv[2])
        safe_sy = sy_id.replace("/", "_")
        outfile = sys.argv[3] if len(sys.argv) >= 4 else f"buecherliste_{safe_sy}_{bl_id}.pdf"
        pdf = client.admin.get_booklist_pdf(sy_id, bl_id)
        with open(outfile, "wb") as f:
            f.write(pdf)
        print(f"PDF gespeichert: {outfile} ({len(pdf):,} Bytes)")
    else:
        # Alle Bücherlisten des Schuljahrs
        lists = client.admin.get_booklists(sy_id)
        print(f"{len(lists)} Bücherliste(n) für Schuljahr {sy_id}:")
        for bl in lists:
            print(f"  {json.dumps(bl, ensure_ascii=False)}")
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")
