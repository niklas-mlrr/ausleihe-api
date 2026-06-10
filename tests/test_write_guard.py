"""Tests für den Read-only-Write-Guard des AusleiheClient.

Sicherheitskritisch: Diese API zeigt auf die PRODUKTION der Schule. Non-GET-
Requests müssen standardmäßig (ohne allow_writes=True) blockiert werden, BEVOR
ein Netzwerk-Request rausgeht. Die Tests bauen den Client per __new__ ohne Login
auf — es wird also nie eine echte Verbindung geöffnet.
"""
import pytest

from ausleihe import AusleiheClient, AusleiheError


def _bare_client(allow_writes: bool) -> AusleiheClient:
    """Client ohne __init__/_login (kein Netzwerk) — nur der Write-Guard wird getestet."""
    client = AusleiheClient.__new__(AusleiheClient)
    client._allow_writes = allow_writes
    return client


@pytest.mark.parametrize("call_name", ["put", "post"])
def test_writes_blocked_by_default(call_name):
    client = _bare_client(allow_writes=False)
    with pytest.raises(AusleiheError) as excinfo:
        getattr(client, call_name)("/studentids/x", json={"student": 1})
    assert "Schreibende Requests" in str(excinfo.value)


def test_write_guard_passes_with_allow_writes():
    # Mit allow_writes=True greift der Guard nicht mehr; der Aufruf scheitert erst
    # später (kein echter Session-State), aber NICHT mit der Write-Guard-Meldung.
    client = _bare_client(allow_writes=True)
    with pytest.raises(Exception) as excinfo:
        client.put("/studentids/x", json={"student": 1})
    assert "Schreibende Requests" not in str(excinfo.value)
