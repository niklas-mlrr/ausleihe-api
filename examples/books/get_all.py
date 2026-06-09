"""
Alle Bücher abrufen.

Verwendung:
  python3 examples/books/get_all.py
  python3 examples/books/get_all.py --deleted   # gelöschte Bücher einschließen
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client

include_deleted = "--deleted" in sys.argv

client = make_client()
books = client.books.get_all(include_deleted=include_deleted)

print(f"Bücher gesamt: {len(books)}")
print(f"Verfügbar:     {sum(1 for b in books if b.available)}")
print(f"Ausgeliehen:   {sum(1 for b in books if b.distributed)}")
print(f"Gelöscht:      {sum(1 for b in books if b.deleted)}")
print()
print("Erste 5 Einträge:")
for b in books[:5]:
    title = b.series.title if b.series else b.isbn
    status = "verfügbar" if b.available else ("ausgeliehen" if b.distributed else "unbekannt")
    print(f"  [{b.code}] {title[:60]} — {status}")
