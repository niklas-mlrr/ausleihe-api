# Bestand- und Nachbestellungen — Excel-Tooling

Aktualisiert die Excel-Bestands- und Nachbestellungsliste aus der IServ-Ausleihe-API
(rein lesend, nur GET).

## Für Nachfolger — nur dieses Skript verwenden

| Pfad | Status | Verwendung |
|------|--------|------------|
| **`New - API approach/update_bestand_auto.py`** | ✅ **aktuell** | **Das einzige Skript, das Nachfolger brauchen.** Auto-Discovery: liest die Excel-Struktur selbst aus, braucht keine `config.json`. |
| `New - API approach/update_bestand.py` | ⚠️ veraltet | Älterer Ansatz mit manuell gepflegter `config.json` (ISBN↔Zellen-Mappings). Funktioniert noch, ist aber fehleranfällig bei neuen Buchreihen. **Nicht mehr verwenden** — `update_bestand_auto.py` ist der Ersatz. |
| `Old - Webscraper for Excel/` | 🗑️ abgelöst | Scrapte das IServ-Frontend statt der API. **Nicht verwenden.** Nur als historischer Bezug behalten. |

## Schnellstart (für Nachfolger)

```bash
cd "bestand- und nachbestellungen/New - API approach"

# 1) Erst prüfen, ohne zu schreiben (Trockenlauf):
python3 update_bestand_auto.py --dry-run --excel "Bestand- und Nachbestellungsliste 2026.xlsx" -v

# 2) Wenn alles plausibel aussieht, wirklich ausführen:
python3 update_bestand_auto.py --excel "Bestand- und Nachbestellungsliste 2026.xlsx"
```

Voraussetzungen: installiertes `ausleihe-api` (siehe übergeordnetes Repo), `.env`
mit IServ-Zugangsdaten im `ausleihe-api`-Root, sowie `openpyxl` + `isbnlib`
(`pip install -e ".[bestand]"` im `ausleihe-api`-Root).

Die vollständige Anleitung für Nachfolger (inkl. Ersteinrichtung und typischer
Fehler) liegt im Schwester-Projekt unter
`ausleihe-ausgabe/docs/nachfolge-anleitung.md` (Teil 3).

## Wichtiger Hinweis zur Lebensdauer

Das Skript greift auf die IServ-Ausleihe-API zu, die nicht offiziell dokumentiert ist
und sich jederzeit ändern kann. Wenn die IServ-Website/API aktualisiert wird, kann
das Skript Buchreihen nicht mehr korrekt zuordnen (insbesondere bei neuen oder
umbenannten Fächern). Das ist kein Fehler der Anwenderin/des Anwenders — siehe
Fehler-Abschnitt in der Nachfolge-Anleitung.