"""
Ausgeliehene Bücher eines Schülers abrufen.

Verwendung:
  python3 examples/students/get_books.py <id>
  python3 examples/students/get_books.py 2167
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, NotFoundError, die

if len(sys.argv) < 2:
    die("Verwendung: get_books.py <id>")

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
