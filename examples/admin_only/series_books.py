"""
Alle Exemplare einer Buchserie abrufen. [Admin]

Verwendung:
  python3 -m examples.admin_only.series_books <isbn>
  python3 -m examples.admin_only.series_books 9783507887435
"""
import sys

from examples._common import ForbiddenError, die, make_client

if len(sys.argv) < 2:
    die("Verwendung: python3 -m examples.admin_only.series_books <isbn>")

client = make_client()

try:
    books = client.admin.get_series_books(sys.argv[1])
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(books)} Exemplar(e) für ISBN {sys.argv[1]}:")
for b in books:
    status = "verfügbar" if b.available else ("ausgeliehen" if b.distributed else "unbekannt")
    print(f"  [{b.code}] {status:<12} Ausleihen: {b.issuances}")
