"""
Einzelnes Buch nach Barcode-Code abrufen.

Verwendung:
  python3 examples/books/get_by_code.py <code>
  python3 examples/books/get_by_code.py 00015193
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, NotFoundError, die

if len(sys.argv) < 2:
    die("Verwendung: get_by_code.py <code>")

code = sys.argv[1]
client = make_client()

try:
    b = client.books.get_by_code(code)
except NotFoundError:
    die(f"Kein Buch mit Code '{code}' gefunden.")

title = b.series.title if b.series else b.isbn
publisher = b.series.publisher if b.series else "-"

print(f"Code:      {b.code}")
print(f"Titel:     {title}")
print(f"ISBN:      {b.isbn}")
print(f"Verlag:    {publisher}")
print(f"Status:    {'verfügbar' if b.available else 'ausgeliehen'}")
print(f"Gelöscht:  {b.deleted}")
print(f"Inventar:  {b.inventory}")
print(f"Ausleihen: {b.issuances} gesamt, {b.long_issuances} Langzeit")

if b.distributed:
    since = b.distributed_at.strftime("%d.%m.%Y %H:%M") if b.distributed_at else "unbekannt"
    print(f"Ausleiher: {b.distributed_by} (seit {since})")
    if b.student:
        s = b.student
        print(f"Schüler:   {s.firstname} {s.lastname} (ID: {s.id})")

print(f"Erstellt:  {b.created_at.strftime('%d.%m.%Y') if b.created_at else '-'} von {b.created_by or '-'}")
