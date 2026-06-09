"""
Einzelne Bücherliste mit vollständiger Konfiguration (GET /schoolyears/:id/booklists/:bl_id). [Helfer]

Verwendung:
  python3 examples/schoolyears/booklist_detail.py <schoolyear_id> <booklist_id>
  python3 examples/schoolyears/booklist_detail.py "2025/2026" 42
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die
import json

if len(sys.argv) < 3:
    die('Verwendung: booklist_detail.py <schoolyear_id> <booklist_id>')

client = make_client()
sy_id = sys.argv[1]
bl_id = int(sys.argv[2])

bl = client.schoolyears.get_booklist(sy_id, bl_id)

print(f"Bücherliste [{bl['id']}]: {bl.get('name', bl.get('title', '?'))}")
sections = bl.get("sections", [])
print(f"Abschnitte ({len(sections)}):")
for sec in sections:
    options = sec.get("options", [])
    for opt in options:
        items = opt.get("items", [])
        for item in items:
            sd = item.get("series_data", {})
            title = sd.get("title", item.get("isbn", "?"))
            grades = sd.get("gradesFlat", [])
            print(f"  [{sec.get('name', '?')}] {title}  Jahrgänge: {grades}")
print()
print(json.dumps(bl, indent=2, ensure_ascii=False))
