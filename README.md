# IServ Ausleihe API

Unofficial, read-first Python client for the IServ school-book lending API
(Python 3.10+).
It is reverse engineered and intended for local school administration tooling.

## Installation

```bash
python3 -m pip install -e ".[bestand,dev]"
```

`ISERV_DOMAIN` is always required. `ISERV_USERNAME` and `ISERV_PASSWORD` are
needed only when accessing a protected endpoint. Construction is network-free;
call `client.login()` when an application deliberately wants fail-fast login.

```python
from ausleihe import AusleiheClient

# Public endpoint: no credentials and no login necessary.
client = AusleiheClient(domain="schule.example.de")
rules = client.get_borrowing_rules()
```

The client rejects URLs, paths and ports for `domain`; pass a bare host name.
Requests have a configurable connect/read timeout and only safe read requests
are retried. State-changing requests remain blocked unless `allow_writes=True`.

## Inventory workbook

The supported command is:

```bash
python3 "bestand- und nachbestellungen/New - API approach/update_bestand_auto.py" \
  --dry-run --excel "Bestand- und Nachbestellungsliste 2026.xlsx"
```

Normal runs fail without replacing the workbook if book matching or workbook
structure is ambiguous. Use `match_overrides` in the adjacent `config.json` to
map a `grade|subject|hint` key to a specific ISBN. `safety_stock` is explicit
and defaults to the current operational value of `5`; override it with
`--safety-stock`. Successful saves make a timestamped backup next to the input.

## Development

```bash
python3 -m pytest
python3 -m ruff check ausleihe tests
python3 -m mypy
python3 -m pip_audit
```

Tests must use mocks/fake sessions and generated temporary workbooks. Never use
production credentials or send a write request to the live IServ service.
