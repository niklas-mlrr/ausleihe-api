"""
Bücherlisten-Vergleich vorwärts entlang der mitwachsenden Kohorte. [Helfer]

Vergleicht für einen Jahrgang die ausleihbaren Bücher (borrowable=True), die er
*dieses* Schuljahr hat, mit denen, die *dieselbe Kohorte* im *nächsten* Schuljahr
eine Stufe höher haben wird. Also: Schuljahr X Jahrgang N  gegen  Schuljahr X+1
Jahrgang N+1.

So sieht man pro Kohorte, welche Bücher beim Aufstieg ins nächste Jahr neu
hinzukommen (+) und welche wegfallen (−) — z. B. ob ein durchgehendes Werk
fortgeführt wird oder eine Neuauflage/ein neues Lehrwerk eingeführt wird.

Der höchste Jahrgang wird übersprungen (keine Stufe N+1 im nächsten Schuljahr).
Rein lesend (nur GET).

Verwendung:
  # Aktuelles Schuljahr gegen automatisch ermitteltes Folgejahr:
  python3 examples/schoolyears/compare_cohort_booklists.py
  python3 examples/schoolyears/compare_cohort_booklists.py "2025/2026"

  # Explizit Basisjahr und Folgejahr:
  python3 examples/schoolyears/compare_cohort_booklists.py "2025/2026" "2026/2027"

  # Auch unveränderte Kohorten auflisten:
  python3 examples/schoolyears/compare_cohort_booklists.py --all
"""
import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from _common import make_client, die
from ausleihe.exceptions import NotFoundError


def next_schoolyear(sy_id: str) -> str:
    """'2025/2026' -> '2026/2027'."""
    try:
        begin, end = sy_id.split("/")
        return f"{int(begin) + 1}/{int(end) + 1}"
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
    next_id = args[1] if len(args) >= 2 else next_schoolyear(sy_id)

    try:
        cur_lists = booklists_by_grade(client, sy_id)
        next_lists = booklists_by_grade(client, next_id)
    except NotFoundError as e:
        die(f"Schuljahr nicht gefunden: {e}")

    highest = max(cur_lists) if cur_lists else None

    print(f"Kohorten-Vergleich (vorwärts): {sy_id}  gegen Folgejahr {next_id}")
    print(f"(Jahrgang N {sy_id}  ↔  Jahrgang N+1 {next_id}, nur borrowable=True)")
    print(f"Höchster Jahrgang {highest} übersprungen (kein Folgejahrgang).\n")

    n_changed = 0
    for grade in sorted(cur_lists):
        if grade == highest:
            continue
        cur_bl = cur_lists[grade]
        cur_books = borrowable_books(client, sy_id, cur_bl["id"])

        next_bl = next_lists.get(grade + 1)
        if next_bl is None:
            print(f"Jahrgang {grade} ({sy_id})  ↔  Jahrgang {grade + 1} ({next_id}): "
                  f"kein Folgejahrgang gefunden — übersprungen.\n")
            continue
        next_books = borrowable_books(client, next_id, next_bl["id"])

        added = {i: t for i, t in next_books.items() if i not in cur_books}
        removed = {i: t for i, t in cur_books.items() if i not in next_books}

        if not added and not removed:
            if show_all:
                print(f"Jahrgang {grade} → {grade + 1}: unverändert "
                      f"({len(cur_books)} ausleihbare Titel).\n")
            continue

        n_changed += 1
        print(f"Jahrgang {grade} ({sy_id})  →  Jahrgang {grade + 1} ({next_id}): "
              f"{len(added)} neu, {len(removed)} entfallen "
              f"({len(cur_books)} → {len(next_books)} ausleihbare Titel)")
        for isbn, title in sorted(removed.items(), key=lambda x: x[1].lower()):
            print(f"  − [{isbn}] {title}")
        for isbn, title in sorted(added.items(), key=lambda x: x[1].lower()):
            print(f"  + [{isbn}] {title}")
        print()

    if n_changed == 0:
        print("Keine Veränderungen bei ausleihbaren Büchern entlang der Kohorten.")
    else:
        print(f"Veränderte Kohorten: {n_changed}")


if __name__ == "__main__":
    main()
