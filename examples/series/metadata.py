"""
Metadaten zu Buchserien abrufen: Verlage, Fächer, Jahrgangsstufen.

Verwendung:
  python3 -m examples.series.metadata publishers   # alle Verlage
  python3 -m examples.series.metadata subjects      # alle Unterrichtsfächer
  python3 -m examples.series.metadata grades        # Jahrgangsstufen + Serienzahl
"""
import sys

from examples._common import die, make_client

MODES = ("publishers", "subjects", "grades")

if len(sys.argv) < 2 or sys.argv[1] not in MODES:
    die(f"Verwendung: python3 -m examples.series.metadata <{'|'.join(MODES)}>")

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
