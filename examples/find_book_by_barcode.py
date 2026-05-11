"""Buch nach Barcode suchen und Ausleiher-Info ausgeben."""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from ausleihe import AusleiheClient, NotFoundError

CODE = os.environ.get("BOOK_CODE") or (sys.argv[1] if len(sys.argv) > 1 else "00015193")

client = AusleiheClient()
try:
    book = client.books.get_by_code(CODE)
except NotFoundError:
    print(f"Kein Buch mit Code {CODE} gefunden.")
    sys.exit(1)

title = book.series.title if book.series else book.isbn
print(f"Code:    {book.code}")
print(f"Titel:   {title}")
print(f"ISBN:    {book.isbn}")
print(f"Status:  {'verfügbar' if book.available else 'ausgeliehen'}")

if book.distributed and book.student:
    s = book.student
    print(f"Ausleiher: {s.firstname} {s.lastname} ({s.iserv_act})")
    if book.distributed_at:
        print(f"Seit:    {book.distributed_at.strftime('%d.%m.%Y %H:%M')}")
elif book.distributed_by:
    print(f"Ausleiher: {book.distributed_by}")

print(f"Ausleihen gesamt: {book.issuances} (davon lang: {book.long_issuances})")
