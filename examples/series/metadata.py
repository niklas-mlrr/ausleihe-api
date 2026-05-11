"""
Metadaten zu Buchserien abrufen: Verlage, Fächer, Jahrgangsstufen.

Verwendung:
  python3 examples/series/metadata.py publishers
  python3 examples/series/metadata.py subjects
  python3 examples/series/metadata.py grades
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die

MODES = ("publishers", "subjects", "grades")

if len(sys.argv) < 2 or sys.argv[1] not in MODES:
    die(f"Verwendung: metadata.py <{'|'.join(MODES)}>")

mode = sys.argv[1]
client = make_client()

if mode == "publishers":
    items = client.series.get_publishers()
    print(f"{len(items)} Verlage:")
    for p in sorted(items):
        print(f"  {p}")

elif mode == "subjects":
    items = client.series.get_subjects()
    print(f"{len(items)} Unterrichtsfächer:")
    for s in sorted(items):
        print(f"  {s}")

else:
    grades = client.series.get_grades()
    print(f"{len(grades)} Jahrgangsstufen:")
    for g in grades:
        print(f"  Jg. {g['grade']:>2}  →  {g['count_series']} Serien")
