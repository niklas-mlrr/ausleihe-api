# IServ Ausleihe API

Unofficial, read-first Python client for the IServ school-book lending API
(Python 3.10+).
It is reverse engineered and intended for local school administration tooling.

## Installation

```bash
python3 -m pip install -e ".[dev]"
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

## Inventory workbook and book lists

The Excel inventory tooling and the per-subject book-list generator live in a
separate repository, [`sba-bestand`](https://github.com/niklas-mlrr/sba-bestand)
(until 2026-08-21 they were the `bestand- und nachbestellungen/` and
`buecherlisten-nach-fach/` folders here). Clone it next to this repo:

```
<any-folder>/
├── ausleihe-api/     <- this repo (client + .env)
└── sba-bestand/      <- Excel tooling
```

`ausleihe.inventory_excel` keeps `match_book`, the ambiguity check that must not
silently pick the first of several books. `atomic_save_workbook` moved to
`bestand.core.excel_io` in `sba-bestand` on 2026-09-04: it touches only the
filesystem and openpyxl, so making a durable workbook save depend on this API
client was the wrong boundary.

## Development

```bash
python3 -m pytest
python3 -m ruff check ausleihe tests
python3 -m mypy
python3 -m pip_audit
```

Tests must use mocks/fake sessions and generated temporary workbooks. Never use
production credentials or send a write request to the live IServ service.
