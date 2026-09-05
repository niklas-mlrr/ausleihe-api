"""
Bücher clientseitig filtern.

Verwendung:
  # Nach ISBN filtern:
  python3 -m examples.books.filter isbn <isbn>
  python3 -m examples.books.filter isbn 9783507887435

  # Nach Schüler-ID filtern:
  python3 -m examples.books.filter student <id>
  python3 -m examples.books.filter student 2167

  # Nur verfügbare bzw. nur ausgeliehene Bücher:
  python3 -m examples.books.filter available
  python3 -m examples.books.filter distributed
"""
import sys

from examples._common import die, make_client

MODES = ("isbn", "student", "available", "distributed")

if len(sys.argv) < 2 or sys.argv[1] not in MODES:
    die(f"Verwendung: python3 -m examples.books.filter <{'|'.join(MODES)}> [wert]")

mode = sys.argv[1]
client = make_client()

if mode == "isbn":
    if len(sys.argv) < 3:
        die("Verwendung: python3 -m examples.books.filter isbn <isbn>")
    books = client.books.filter_by_isbn(sys.argv[2])
    label = f"ISBN {sys.argv[2]}"

elif mode == "student":
    if len(sys.argv) < 3:
        die("Verwendung: python3 -m examples.books.filter student <id>")
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
