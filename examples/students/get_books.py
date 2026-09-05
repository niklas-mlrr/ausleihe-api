"""
Ausgeliehene Bücher eines Schülers abrufen.

Verwendung:
  python3 -m examples.students.get_books <id>
  python3 -m examples.students.get_books 2167
"""
import sys

from examples._common import NotFoundError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.students.get_books <id>")

student_id = int(sys.argv[1])
client = make_client()

try:
    student = client.students.get_by_id(student_id)
except NotFoundError:
    die(f"Kein Schüler mit ID {student_id} gefunden.")

books = client.students.get_books(student_id)

print(f"Schüler: {student.firstname} {student.lastname} ({student.iserv_act})")
print(f"Ausgeliehene Bücher: {len(books)}")
print()

for b in books:
    title = b.series.title if b.series else b.isbn
    since = b.distributed_at.strftime("%d.%m.%Y") if b.distributed_at else "unbekannt"
    publisher = b.series.publisher if b.series else "-"
    print(f"  [{b.code}] {title}")
    print(f"           Verlag: {publisher} | seit: {since}")
