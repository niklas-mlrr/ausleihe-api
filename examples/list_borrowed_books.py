"""Alle ausgeliehenen Bücher eines Schülers nach Nachname suchen und auflisten."""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()

from ausleihe import AusleiheClient

LASTNAME = os.environ.get("STUDENT_LASTNAME") or (sys.argv[1] if len(sys.argv) > 1 else "")
if not LASTNAME:
    print("Verwendung: python list_borrowed_books.py <Nachname>")
    sys.exit(1)

client = AusleiheClient()
students = client.students.search_by_name(lastname=LASTNAME)

if not students:
    print(f"Kein Schüler mit Nachname '{LASTNAME}' gefunden.")
    sys.exit(0)

for student in students:
    print(f"\n=== {student.firstname} {student.lastname} (ID: {student.id}) ===")
    books = client.students.get_books(student.id)
    if not books:
        print("  Keine ausgeliehenen Bücher.")
        continue
    for book in books:
        title = book.series.title if book.series else book.isbn
        since = book.distributed_at.strftime("%d.%m.%Y") if book.distributed_at else "unbekannt"
        print(f"  [{book.code}] {title}")
        print(f"           seit {since}")
