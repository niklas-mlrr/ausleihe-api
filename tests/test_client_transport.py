from __future__ import annotations

import json

import pytest
import requests

from ausleihe import AusleiheClient, AuthError, ConfigurationError, TransportError


class Response:
    def __init__(self, status: int = 200, payload=None, content: bytes | None = None, headers=None):
        self.status_code = status
        self._payload = payload
        value = payload if payload is not None else {}
        self.content = content if content is not None else json.dumps(value).encode()
        self.text = self.content.decode(errors="replace")
        self.headers = headers or {}
        self.url = "https://schule.example.de/iserv/login"
        self.closed = False

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    def close(self):
        self.closed = True


class Session:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.cookies = {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_public_endpoint_is_lazy_and_uses_timeout():
    session = Session([Response(payload=[] )])
    client = AusleiheClient(domain="schule.example.de", session=session, timeout=(1, 2), max_retries=0)
    assert client.get_borrowing_rules() == []
    assert len(session.calls) == 1
    assert session.calls[0][1].endswith("/borrowing-rules")
    assert session.calls[0][2]["timeout"] == (1, 2)


def test_protected_endpoint_without_credentials_fails_before_network():
    session = Session([])
    client = AusleiheClient(domain="schule.example.de", session=session)
    with pytest.raises(ConfigurationError):
        client.get("/series")
    assert not session.calls


@pytest.mark.parametrize(
    "domain", ["https://schule.example.de", "schule.example.de/x", "schule.example.de:443", "localhost"]
)
def test_invalid_domains_are_rejected(domain):
    with pytest.raises(ConfigurationError):
        AusleiheClient(domain=domain)


def test_safe_get_retries_transient_status(monkeypatch):
    monkeypatch.setattr("ausleihe.client.time.sleep", lambda _: None)
    session = Session([Response(503), Response(payload=[])])
    client = AusleiheClient(domain="schule.example.de", session=session, max_retries=1)
    assert client.get_borrowing_rules() == []
    assert len(session.calls) == 2


def test_negative_retry_after_never_sleeps_a_negative_duration(monkeypatch):
    delays = []
    monkeypatch.setattr("ausleihe.client.time.sleep", delays.append)
    session = Session([Response(503, headers={"Retry-After": "-8"}), Response(payload=[])])
    client = AusleiheClient(domain="schule.example.de", session=session, max_retries=1)
    assert client.get_borrowing_rules() == []
    assert delays == [0.0]


def test_non_get_is_not_retried(monkeypatch):
    monkeypatch.setattr("ausleihe.client.time.sleep", lambda _: None)
    session = Session([Response(503)])
    client = AusleiheClient(domain="schule.example.de", allow_writes=True, session=session, max_retries=2)
    client._jwt, client._jwt_exp = "test", 9999999999
    with pytest.raises(Exception):
        client.post("/x")
    assert len(session.calls) == 1


def test_network_timeout_becomes_domain_error():
    session = Session([requests.Timeout("late")])
    client = AusleiheClient(domain="schule.example.de", session=session, max_retries=0)
    with pytest.raises(TransportError):
        client.get_borrowing_rules()


def test_second_401_for_safe_request_is_auth_error():
    client = AusleiheClient.__new__(AusleiheClient)
    # Exercise the terminal branch without attempting a login.
    client._allow_writes = False
    client._api_base = "https://ausleihe-api.schule.example.de/"
    client._max_retries = 0
    client._timeout = 1
    client._jwt = "test"
    client._jwt_exp = 9999999999
    client._session = Session([Response(401)])
    with pytest.raises(AuthError):
        client._send("GET", "/x", _reauth=False)
