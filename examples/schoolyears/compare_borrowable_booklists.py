"""
Bücherlisten-Vergleich Jahr ↔ Vorjahr: ausleihbare Bücher pro Jahrgang. [Helfer]

Zeigt für jeden Jahrgang, welche *ausleihbaren* Bücher (borrowable=True) gegenüber
dem Vorjahr hinzugekommen oder weggefallen sind. Gedacht für die Überprüfung zur
Einführung neuer Lehrwerke / Neuauflagen: Eine Neuauflage erscheint typischerweise
als weggefallene alte ISBN + neu hinzugekommene ISBN im selben Jahrgang.

Verglichen wird gleicher Jahrgang gegen gleichen Jahrgang (über das Feld `grade`
der Bücherliste), nicht die mitwachsende Kohorte. Nur ausleihbare Titel zählen;
Kauf-/Arbeitshefte (borrowable=False) werden ignoriert.

Verwendung:
  # Aktuelles Schuljahr gegen automatisch ermitteltes Vorjahr:
  python3 -m examples.schoolyears.compare_borrowable_booklists
  python3 -m examples.schoolyears.compare_borrowable_booklists "2025/2026"

  # Explizit Jahr und Vorjahr angeben:
  python3 -m examples.schoolyears.compare_borrowable_booklists "2025/2026" "2024/2025"

  # Auch unveränderte Jahrgänge auflisten:
  python3 -m examples.schoolyears.compare_borrowable_booklists --all
"""
import sys

from ausleihe.exceptions import NotFoundError
from examples._common import die, make_client


def previous_schoolyear(sy_id: str) -> str:
    """'2025/2026' -> '2024/2025'."""
    try:
        begin, end = sy_id.split("/")
        return f"{int(begin) - 1}/{int(end) - 1}"
    except (ValueError, IndexError):
        die(f'Schuljahr-ID nicht im Format "YYYY/YYYY": {sy_id!r}')


def borrowable_books(client, sy_id: str, booklist_id: int) -> dict[str, str]:
    """ISBN -> Titel aller ausleihbaren Bücher einer Bücherliste."""
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
    return books


def booklists_by_grade(client, sy_id: str) -> dict[int, dict]:
    """grade -> Bücherlisten-Metadaten des Schuljahrs."""
    by_grade: dict[int, dict] = {}
    for bl in client.schoolyears.get_booklists(sy_id):
        grade = bl.get("grade")
        if grade is not None:
            by_grade[grade] = bl
    return by_grade


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    show_all = "--all" in sys.argv[1:]

    client = make_client()

    sy_id = args[0] if len(args) >= 1 else client.schoolyears.get_current()["id"]
    prev_id = args[1] if len(args) >= 2 else previous_schoolyear(sy_id)

    try:
        cur_lists = booklists_by_grade(client, sy_id)
        prev_lists = booklists_by_grade(client, prev_id)
    except NotFoundError as e:
        die(f"Schuljahr nicht gefunden: {e}")

    print(f"Vergleich ausleihbarer Bücher: {sy_id}  gegen Vorjahr {prev_id}")
    print(f"(gleicher Jahrgang ↔ gleicher Jahrgang, nur borrowable=True)\n")

    n_changed = 0
    for grade in sorted(cur_lists):
        cur_bl = cur_lists[grade]
        cur_books = borrowable_books(client, sy_id, cur_bl["id"])

        prev_bl = prev_lists.get(grade)
        if prev_bl is None:
            print(f"Jahrgang {grade}: kein Pendant im Vorjahr {prev_id} — übersprungen.\n")
            continue
        prev_books = borrowable_books(client, prev_id, prev_bl["id"])

        added = {i: t for i, t in cur_books.items() if i not in prev_books}
        removed = {i: t for i, t in prev_books.items() if i not in cur_books}

        if not added and not removed:
            if show_all:
                print(f"Jahrgang {grade}: unverändert ({len(cur_books)} ausleihbare Titel).\n")
            continue

        n_changed += 1
        print(f"Jahrgang {grade}: {len(added)} neu, {len(removed)} entfallen "
              f"({len(prev_books)} → {len(cur_books)} ausleihbare Titel)")
        for isbn, title in sorted(removed.items(), key=lambda x: x[1]):
            print(f"  − [{isbn}] {title}")
        for isbn, title in sorted(added.items(), key=lambda x: x[1]):
            print(f"  + [{isbn}] {title}")
        print()

    if n_changed == 0:
        print("Keine Veränderungen bei ausleihbaren Büchern gegenüber dem Vorjahr.")
    else:
        print(f"Veränderte Jahrgänge: {n_changed}")


if __name__ == "__main__":
    main()
