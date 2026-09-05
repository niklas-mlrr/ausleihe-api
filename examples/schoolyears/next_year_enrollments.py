"""
READ-ONLY: Anmeldungen (enrollments) für das kommende Schuljahr abrufen.

Macht ausschliesslich GET-Requests. Es werden KEINE Daten geaendert/angelegt.

Verwendung:
  python3 -m examples.schoolyears.next_year_enrollments
"""
import json
from collections import Counter

from examples._common import ForbiddenError, make_client

client = make_client()

# 1. Alle Schuljahre (GET, read-only)
years = client.admin.get_schoolyears()
ids = [y.get("id") for y in years]
print("Vorhandene Schuljahre:", ", ".join(str(i) for i in ids))

current = client.schoolyears.get_current()
cur_id = current.get("id")
print(f"Aktuelles Schuljahr: {cur_id}")
print(f"  enrollment_enabled={current.get('enrollment_enabled')} "
      f"enrollment_begin={current.get('enrollment_begin')} "
      f"enrollment_end={current.get('enrollment_end')}")

# 2. Naechstes Schuljahr bestimmen (cur 'YYYY/YYYY+1' -> +1)
def next_of(sy_id):
    try:
        a, b = sy_id.split("/")
        return f"{int(a)+1}/{int(b)+1}"
    except Exception:
        return None

target = next_of(cur_id)
print(f"\nGesuchtes Folge-Schuljahr: {target}")
if target not in ids:
    print(f"  -> {target} ist noch NICHT als Schuljahr angelegt.")
    # Trotzdem versuchen, evtl. existiert es ohne in der Liste zu sein
# Metadaten des Zieljahres (falls vorhanden)
ty = next((y for y in years if y.get("id") == target), None)
if ty:
    print(f"  enrollment_enabled={ty.get('enrollment_enabled')} "
          f"enrollment_begin={ty.get('enrollment_begin')} "
          f"enrollment_end={ty.get('enrollment_end')} "
          f"archived_at={ty.get('archived_at')}")

# 3. Anmeldungen des Zieljahres (GET, read-only)
print(f"\n--- Anmeldungen {target} ---")
try:
    enr = client.admin.get_enrollments(target)
    print(f"Anzahl Anmeldungen: {len(enr)}")
    if enr:
        # Aggregat: nach Jahrgangsstufe (upcoming_grade)
        grades = Counter(str(e.get("student_upcoming_grade")) for e in enr)
        forms = Counter(str(e.get("student_upcoming_form")) for e in enr)
        print("Nach Jahrgangsstufe:", dict(sorted(grades.items())))
        print("Nach Klasse:", dict(sorted(forms.items())))
        sample = enr[0]
        print("\nBeispiel-Anmeldung (Schluessel):")
        print("  " + ", ".join(sorted(sample.keys())))
except ForbiddenError:
    print("403 - kein Zugriff (Verwalter-Rolle noetig).")
except Exception as e:
    print(f"Fehler: {type(e).__name__}: {e}")

# 4. Vergleich: aktuelles Jahr zur Einordnung (read-only)
print(f"\n--- Anmeldungen aktuelles Jahr {cur_id} (Referenz) ---")
try:
    enr_cur = client.admin.get_enrollments(cur_id)
    print(f"Anzahl Anmeldungen: {len(enr_cur)}")
except Exception as e:
    print(f"Fehler: {type(e).__name__}: {e}")
