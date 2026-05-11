# iserv-ausleihe-api

> **Inoffizieller** Python-Client für die IServ Schulbuchausleihe REST API.
> Reverse-engineered aus dem Angular-Frontend. Nicht von IServ / Dataport unterstützt oder autorisiert.

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)
![MIT License](https://img.shields.io/badge/license-MIT-green)

## Disclaimer

Diese Library ist ein inoffizielles Reverse-Engineering-Projekt und steht in keiner Verbindung zu IServ GmbH oder Dataport. Die API ist nicht dokumentiert und kann sich jederzeit ohne Vorankündigung ändern. Verwendung auf eigene Verantwortung.

## Installation

```bash
pip install -e .
```

Oder direkt als Abhängigkeit:

```bash
pip install git+https://github.com/yourname/iserv-ausleihe-api.git
```

## Quick Start

```python
from dotenv import load_dotenv
from ausleihe import AusleiheClient

load_dotenv()  # ISERV_DOMAIN, ISERV_USERNAME, ISERV_PASSWORD aus .env

client = AusleiheClient()

# Buch nach Barcode
book = client.books.get_by_code("00015193")
print(book.series.title, "→", "verfügbar" if book.available else "ausgeliehen")

# Ausgeliehene Bücher eines Schülers
students = client.students.search_by_name(lastname="Mustermann")
books = client.students.get_books(students[0].id)
for b in books:
    print(b.code, b.series.title if b.series else b.isbn)
```

## Konfiguration

Credentials werden aus Umgebungsvariablen gelesen (`.env`-Datei empfohlen):

```env
ISERV_DOMAIN=iserv-trg-oha.de
ISERV_USERNAME=dein.benutzername
ISERV_PASSWORD=dein_passwort
```

Alternativ direkt im Konstruktor:

```python
client = AusleiheClient(
    domain="iserv-trg-oha.de",
    username="benutzername",
    password="passwort",
)
```

## Auth-Flow

Die Library übernimmt den gesamten Authentifizierungsprozess automatisch:

1. GET `/iserv/login` — OAuth2/OpenID-Connect-Redirect-Kette folgen, CSRF-Token holen
2. POST `/iserv/auth/login` — Credentials + CSRF-Token senden, Session-Cookie erhalten
3. POST `/iserv/ausleihe/session` — JWT + Ablaufzeit holen
4. Alle API-Requests mit `Authorization: Bearer <jwt>`

JWT-Refresh läuft automatisch: 60 Sekunden vor Ablauf wird ein neues Token geholt. Bei 401 wird einmalig ein Retry mit frischem Token durchgeführt.

## API Reference

### `AusleiheClient`

```python
AusleiheClient(domain=None, username=None, password=None)
```

| Property | Typ | Beschreibung |
|----------|-----|--------------|
| `client.books` | `BookAPI` | Bücher-Endpunkte |
| `client.students` | `StudentAPI` | Schüler-Endpunkte |
| `client.series` | `SeriesAPI` | Buchserien-Endpunkte |
| `client.users` | `UserAPI` | IServ-Nutzer-Endpunkte |

```python
client.get_borrowing_rules() -> list[dict]
client.get_loan_slip_pdf(student_id, variant, start_reporting_period, doublepage) -> bytes
```

---

### `BookAPI` — `client.books`

| Methode | Rückgabe | Beschreibung |
|---------|----------|--------------|
| `get_all(include_deleted=False)` | `list[Book]` | Alle Exemplare (gecacht, 5 min) |
| `get_by_code(code)` | `Book` | Einzelnes Exemplar nach Barcode |
| `filter_by_isbn(isbn)` | `list[Book]` | Alle Exemplare einer Serie (clientseitig) |
| `filter_by_student(student_id)` | `list[Book]` | Alle Bücher eines Ausleihers (clientseitig) |
| `filter_available()` | `list[Book]` | Verfügbare Exemplare (clientseitig) |
| `filter_distributed()` | `list[Book]` | Verliehene Exemplare (clientseitig) |
| `invalidate_cache()` | `None` | Cache manuell leeren |

---

### `StudentAPI` — `client.students`

| Methode | Rückgabe | Beschreibung |
|---------|----------|--------------|
| `get_all(include_deleted=False)` | `list[Student]` | Alle Schüler |
| `get_by_id(student_id)` | `Student` | Einzelner Schüler nach ID |
| `get_books(student_id)` | `list[Book]` | Ausgeliehene Bücher eines Schülers |
| `search_by_name(lastname="", firstname="")` | `list[Student]` | Suche nach Name |

---

### `SeriesAPI` — `client.series`

| Methode | Rückgabe | Beschreibung |
|---------|----------|--------------|
| `get_all()` | `list[Series]` | Alle Buchserien (296) |
| `get_by_isbn(isbn)` | `Series` | Serie mit total/available-Feldern |
| `get_publishers()` | `list[str]` | Alle Verlage |
| `get_subjects()` | `list[str]` | Alle Unterrichtsfächer |
| `get_grades()` | `list[dict]` | Jahrgangsstufen mit Anzahl Serien |

---

### `UserAPI` — `client.users`

| Methode | Rückgabe | Beschreibung |
|---------|----------|--------------|
| `get_all()` | `list[dict]` | Alle IServ-Nutzer (808) |
| `search_by_name(lastname="", firstname="")` | `list[dict]` | Suche nach Name |

---

## Endpunkte-Übersicht

| Methode | Pfad | Beschreibung | Rolle |
|---------|------|--------------|-------|
| GET | `/books` | Alle Exemplare | Helfer |
| GET | `/books/:code` | Einzelnes Exemplar | Helfer |
| GET | `/students` | Alle Schüler | Helfer |
| GET | `/students/:id` | Einzelner Schüler | Helfer |
| GET | `/students/:id/books` | Ausgeliehene Bücher | Helfer |
| GET | `/students/:id/claims` | Forderungen | Helfer+ |
| GET | `/series` | Alle Buchserien | Helfer |
| GET | `/series/:isbn` | Serie mit Verfügbarkeit | Helfer |
| GET | `/series/publishers` | Verlage | Helfer |
| GET | `/series/subjects` | Fächer | Helfer |
| GET | `/series/grades` | Jahrgangsstufen | Helfer |
| GET | `/iserv/users` | IServ-Nutzer | Helfer |
| GET | `/borrowing-rules` | Ausleihregeln | — (öffentlich) |
| GET | `/loan-slips` | Leihschein PDF | Helfer |
| GET | `/schoolyears` | Schuljahre | Admin |
| GET | `/settings` | Systemeinstellungen | Admin |
| GET | `/claims` | Alle Forderungen | Admin |
| GET | `/bank` | Bankverbindungen | Admin |
| GET | `/transactions` | Zahlungstransaktionen | Admin |
| GET | `/series/:isbn/books` | Exemplare einer Serie | Admin |

## Datenmodelle

### `Book`

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `code` | `str` | Barcode (eindeutig) |
| `isbn` | `str` | ISBN-13 der Serie |
| `available` | `bool` | Verfügbar |
| `distributed` | `bool` | Aktuell verliehen |
| `distributed_id` | `int \| None` | ID des Ausleihvorgangs |
| `distributed_by` | `str \| None` | IServ-Act des Ausleihers |
| `distributed_at` | `datetime \| None` | Ausgabezeitpunkt |
| `deleted` | `bool` | Ausgesondert |
| `student_id` | `int \| None` | ID des aktuellen Ausleihers |
| `issuances` | `int` | Gesamtausleihen |
| `long_issuances` | `int` | Davon Langzeitausleihen |
| `inventory` | `bool` | Im Inventar |
| `imported` | `bool` | Importiertes Exemplar |
| `text` | `str \| None` | Freitextnotiz |
| `created_by` | `str \| None` | Erstellt von (IServ-Act) |
| `created_at` | `datetime \| None` | Erstellungszeitpunkt |
| `series` | `Series \| None` | Zugehörige Buchserie |
| `student` | `Student \| None` | Aktueller Ausleiher |

### `Student`

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `id` | `int` | Interne ID |
| `firstname` | `str` | Vorname |
| `lastname` | `str` | Nachname |
| `iserv_act` | `str` | IServ-Benutzername |
| `date_of_birth` | `datetime \| None` | Geburtsdatum |
| `left` | `datetime \| None` | Austrittsdatum |
| `anonymized_at` | `datetime \| None` | Anonymisierungsdatum |
| `import_id` | `str \| None` | ID im Quellsystem |
| `created_at` | `datetime \| None` | Erstellungszeitpunkt |

### `Series`

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `isbn` | `str` | ISBN-13 (eindeutig) |
| `title` | `str` | Titel |
| `publisher` | `str` | Verlag |
| `price` | `float` | Neupreis in EUR |
| `fee` | `float` | Leihgebühr in EUR |
| `abolished` | `bool` | Nicht mehr im Einsatz |
| `grades` | `list[int]` | Jahrgangsstufen |
| `subjects` | `list[str]` | Unterrichtsfächer |
| `total` | `int \| None` | Exemplare gesamt (nur bei `get_by_isbn`) |
| `available` | `int \| None` | Verfügbar (nur bei `get_by_isbn`) |

## Bekannte Limitierungen

- **Kein serverseitiges Filtering:** Query-Parameter wie `?isbn=` oder `?student=` werden von der API ignoriert. Alle `filter_*`-Methoden arbeiten clientseitig auf dem vollständig geladenen Datensatz.
- **Kein Paging:** `/books` liefert alle ~18.000 Exemplare in einem Response. Der erste Aufruf dauert entsprechend länger; nachfolgende Aufrufe nutzen den eingebauten Cache (5 Minuten TTL).
- **JWT-Ablauf:** JWT läuft nach ca. 45 Minuten ab. Die Library erneuert ihn automatisch, solange der Session-Cookie gültig ist. Läuft auch der Cookie ab, ist ein erneuter Login (neues `AusleiheClient()`-Objekt) nötig.
- **Admin-Endpunkte:** Endpunkte wie `/schoolyears`, `/claims`, `/settings` sind nur mit `mod_sbl_role_manager`-Berechtigung zugänglich und werden von dieser Library nicht explizit gewrappt.
- **CORS:** Die API akzeptiert nur Requests vom Frontend-Origin. Die Library setzt den `Origin`-Header automatisch korrekt.

## Lizenz

MIT License — siehe [LICENSE](LICENSE)
