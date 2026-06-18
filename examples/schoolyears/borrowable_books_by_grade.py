"""
Ausleihbare Bücher je Jahrgang eines Schuljahrs auflisten. [Helfer]

Listet für jeden Jahrgang (= Bücherliste) die ausleihbaren Titel (borrowable=True)
auf. Kauf-/Arbeitshefte (borrowable=False) werden ignoriert. Rein lesend (nur GET).

Verwendung:
  # Aktuelles Schuljahr:
  python3 examples/schoolyears/borrowable_books_by_grade.py
  python3 examples/schoolyears/borrowable_books_by_grade.py "2025/2026"

  # Nur einen Jahrgang:
  python3 examples/schoolyears/borrowable_books_by_grade.py "2025/2026" 7
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die
from ausleihe.exceptions import NotFoundError


def borrowable_books(client, sy_id: str, booklist_id: int) -> list[tuple[str, str]]:
    """(ISBN, Titel) aller ausleihbaren Bücher einer Bücherliste, alphabetisch."""
    bl = client.schoolyears.get_booklist(sy_id, booklist_id)
    books: dict[str, str] = {}
    for sec in bl.get("sections", []):
        for opt in sec.get("options", []):
            for item in opt.get("items", []):
                if not item.get("borrowable"):
                    continue
                sd = item.get("series_data", {}) or {}
                isbn = sd.get("isbn") or item.get("series") or "?"
                books[isbn] = sd.get("title", "?")
    return sorted(books.items(), key=lambda x: x[1].lower())


def main() -> None:
    args = sys.argv[1:]
    client = make_client()

    sy_id = args[0] if len(args) >= 1 else client.schoolyears.get_current()["id"]
    only_grade = int(args[1]) if len(args) >= 2 else None

    try:
        booklists = client.schoolyears.get_booklists(sy_id)
    except NotFoundError:
        die(f"Schuljahr nicht gefunden: {sy_id}")

    by_grade = {bl.get("grade"): bl for bl in booklists if bl.get("grade") is not None}

    print(f"Ausleihbare Bücher im Schuljahr {sy_id} (nur borrowable=True)\n")

    total = 0
    for grade in sorted(by_grade):
        if only_grade is not None and grade != only_grade:
            continue
        bl = by_grade[grade]
        books = borrowable_books(client, sy_id, bl["id"])
        total += len(books)
        print(f"Jahrgang {grade} — {len(books)} ausleihbare Titel:")
        for isbn, title in books:
            print(f"  [{isbn}] {title}")
        print()

    if only_grade is not None and only_grade not in by_grade:
        die(f"Kein Jahrgang {only_grade} im Schuljahr {sy_id}.")

    print(f"Gesamt: {total} ausleihbare Titel"
          + (f" in Jahrgang {only_grade}" if only_grade is not None else f" über {len(by_grade)} Jahrgänge"))


if __name__ == "__main__":
    main()
