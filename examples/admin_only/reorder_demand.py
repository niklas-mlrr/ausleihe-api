"""
Nachbestell-Bedarf pro Serie für ein Schuljahr abrufen. [Admin, read-only]

Nativer Endpunkt (GET /stock-reorder/:schoolyear/demand) — Ersatz für das
Excel-Scraping. Liefert pro Serie Aggregate: angemeldet gesamt (countAllAssigned),
vollständig ausgegeben (countComplete), noch nicht zugeordnet (countNotAssigned),
plus eine Aufschlüsselung pro Klasse (statsByForm).

Verwendung:
  python3 examples/admin_only/reorder_demand.py [schoolyear_id]
  python3 examples/admin_only/reorder_demand.py "2025/2026"

schoolyear_id: optional, Format "YYYY/YYYY" (Default = aktuelles Schuljahr).
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die

client = make_client()

sy_id = sys.argv[1] if len(sys.argv) >= 2 else client.schoolyears.get_current()["id"]

try:
    demand = client.admin.get_reorder_demand(sy_id)
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(demand)} Serie(n) im Nachbestell-Bedarf für Schuljahr {sy_id}:\n")
for s in demand:
    st = s.get("stats") or {}
    assigned = st.get("countAllAssigned", 0)
    complete = st.get("countComplete", 0)
    open_count = assigned - complete
    print(f"  {s.get('isbn')}  {s.get('title', '')[:50]:50}  "
          f"angemeldet={assigned:>4}  ausgegeben={complete:>4}  offen={open_count:>4}")
