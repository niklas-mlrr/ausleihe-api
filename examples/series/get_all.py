"""
Alle Buchserien abrufen, oder eine einzelne Serie per ISBN.

Verwendung:
  python3 examples/series/get_all.py
  python3 examples/series/get_all.py <isbn>
  python3 examples/series/get_all.py 9783507887435
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, NotFoundError, die

client = make_client()

if len(sys.argv) >= 2:
    # Einzelne Serie
    try:
        s = client.series.get_by_isbn(sys.argv[1])
    except NotFoundError:
        die(f"Keine Serie mit ISBN {sys.argv[1]} gefunden.")

    print(f"ISBN:       {s.isbn}")
    print(f"Titel:      {s.title}")
    print(f"Verlag:     {s.publisher}")
    print(f"Preis:      {s.price:.2f} € (Leihgebühr: {s.fee:.2f} €)")
    print(f"Jahrgänge:  {', '.join(str(g) for g in s.grades) or '-'}")
    print(f"Fächer:     {', '.join(s.subjects) or '-'}")
    print(f"Abgeschafft: {s.abolished}")
    if s.total is not None:
        print(f"Exemplare:  {s.total} gesamt, {s.available} verfügbar")
else:
    # Alle Serien
    series = client.series.get_all()
    print(f"Buchserien gesamt: {len(series)}")
    print(f"Abgeschafft:       {sum(1 for s in series if s.abolished)}")
    print()
    print("Erste 10 Einträge:")
    for s in series[:10]:
        grades = ", ".join(str(g) for g in s.grades[:3])
        print(f"  {s.isbn}  {s.title[:50]:<50}  Jg. {grades}")
