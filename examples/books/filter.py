"""
Bücher clientseitig filtern.

Verwendung:
  python3 examples/books/filter.py isbn <isbn>
  python3 examples/books/filter.py student <id>
  python3 examples/books/filter.py available
  python3 examples/books/filter.py distributed
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die

MODES = ("isbn", "student", "available", "distributed")

if len(sys.argv) < 2 or sys.argv[1] not in MODES:
    die(f"Verwendung: filter.py <{'|'.join(MODES)}> [wert]")

mode = sys.argv[1]
client = make_client()

if mode == "isbn":
    if len(sys.argv) < 3:
        die("Verwendung: filter.py isbn <isbn>")
    books = client.books.filter_by_isbn(sys.argv[2])
    label = f"ISBN {sys.argv[2]}"

elif mode == "student":
    if len(sys.argv) < 3:
        die("Verwendung: filter.py student <id>")
    books = client.books.filter_by_student(int(sys.argv[2]))
    label = f"Schüler-ID {sys.argv[2]}"

elif mode == "available":
    books = client.books.filter_available()
    label = "verfügbar"

else:
    books = client.books.filter_distributed()
    label = "ausgeliehen"

print(f"{len(books)} Bücher ({label}):")
for b in books[:20]:
    title = b.series.title if b.series else b.isbn
    print(f"  [{b.code}] {title[:65]}")

if len(books) > 20:
    print(f"  ... und {len(books) - 20} weitere.")
