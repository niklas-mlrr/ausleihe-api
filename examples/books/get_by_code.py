"""
Einzelnes Buch nach Barcode-Code abrufen.

Verwendung:
  python3 -m examples.books.get_by_code <code>
  python3 -m examples.books.get_by_code 00015193
"""
import sys

from examples._common import NotFoundError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.books.get_by_code <code>")

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
if b.deleted:
    status = "gelöscht"
elif b.available:
    status = "verfügbar"
else:
    status = "ausgeliehen"
print(f"Status:    {status}")
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
