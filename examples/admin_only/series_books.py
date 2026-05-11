"""
Alle Exemplare einer Buchserie abrufen. [Admin]

Verwendung:
  python3 examples/admin_only/series_books.py <isbn>
  python3 examples/admin_only/series_books.py 9783507887435
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, ForbiddenError, die

if len(sys.argv) < 2:
    die("Verwendung: series_books.py <isbn>")

client = make_client()

try:
    books = client.admin.get_series_books(sys.argv[1])
except ForbiddenError:
    die("Kein Zugriff (403). Verwalter-Rolle benötigt.")

print(f"{len(books)} Exemplar(e) für ISBN {sys.argv[1]}:")
for b in books:
    status = "verfügbar" if b.available else ("ausgeliehen" if b.distributed else "unbekannt")
    print(f"  [{b.code}] {status:<12} Ausleihen: {b.issuances}")
