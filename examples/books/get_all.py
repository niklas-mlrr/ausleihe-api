"""
Alle Bücher abrufen.

Verwendung:
  python3 -m examples.books.get_all
  python3 -m examples.books.get_all --deleted   # gelöschte Bücher einschließen
"""
import sys

from examples._common import make_client

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
