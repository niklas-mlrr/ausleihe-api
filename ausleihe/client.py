from __future__ import annotations

import os
import re
import time
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import urljoin

import requests

from .exceptions import (
    AusleiheError,
    AuthError,
    ConfigurationError,
    ForbiddenError,
    NotFoundError,
    TransportError,
)
from .models import BorrowingRule

if TYPE_CHECKING:
    from .admin import AdminAPI
    from .books import BookAPI
    from .schoolyears import SchoolyearsAPI
    from .series import SeriesAPI
    from .students import StudentAPI
    from .users import UserAPI


_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z0-9-]{2,63}$"
)
_SAFE_RETRY_METHODS = {"GET", "HEAD", "OPTIONS"}
_TRANSIENT_STATUSES = {429, 500, 502, 503, 504}


class AusleiheClient:
    """Read-first client for the unofficial IServ Ausleihe API.

    Construction is deliberately network-free.  Public endpoints can therefore be
    used with just ``domain``; protected endpoints authenticate on first use.  Use
    :meth:`login` when an application wants fail-fast credential validation.
    """

    def __init__(
        self,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        allow_writes: bool = False,
        *,
        timeout: float | tuple[float, float] = (5.0, 30.0),
        max_retries: int = 2,
        session: Optional[requests.Session] = None,
    ) -> None:
        self._domain = self._validate_domain(domain or os.environ.get("ISERV_DOMAIN"))
        self._username = username if username is not None else os.environ.get("ISERV_USERNAME")
        self._password = password if password is not None else os.environ.get("ISERV_PASSWORD")
        self._allow_writes = allow_writes
        self._timeout = self._validate_timeout(timeout)
        if max_retries < 0:
            raise ConfigurationError("max_retries darf nicht negativ sein.")
        self._max_retries = max_retries

        self._api_base = f"https://ausleihe-api.{self._domain}/"
        self._iserv_base = f"https://{self._domain}"
        self._frontend_origin = f"https://ausleihe.{self._domain}"
        self._session = session or requests.Session()
        self._session.headers.update({"Origin": self._frontend_origin})
        self._jwt: Optional[str] = None
        self._jwt_exp = 0.0

        self._books_api: Optional[BookAPI] = None
        self._students_api: Optional[StudentAPI] = None
        self._series_api: Optional[SeriesAPI] = None
        self._users_api: Optional[UserAPI] = None
        self._admin_api: Optional[AdminAPI] = None
        self._schoolyears_api: Optional[SchoolyearsAPI] = None

    @staticmethod
    def _validate_domain(domain: Optional[str]) -> str:
        if not domain:
            raise ConfigurationError("ISERV_DOMAIN bzw. domain ist erforderlich.")
        normalized = domain.strip().rstrip(".").lower()
        if not _DOMAIN_RE.fullmatch(normalized):
            raise ConfigurationError(
                "domain muss ein reiner Hostname wie 'schule.example.de' sein, ohne Schema, Pfad oder Port."
            )
        return normalized

    @staticmethod
    def _validate_timeout(timeout: float | tuple[float, float]) -> float | tuple[float, float]:
        if isinstance(timeout, tuple):
            if len(timeout) != 2 or any(not isinstance(v, (int, float)) or v <= 0 for v in timeout):
                raise ConfigurationError(
                    "timeout muss eine positive Zahl oder ein (connect, read)-Paar sein."
                )
            return timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ConfigurationError("timeout muss positiv sein.")
        return timeout

    @staticmethod
    def _extract_form_inputs(html: str) -> dict[str, str]:
        class _Parser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.inputs: dict[str, str] = {}

            def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
                if tag.lower() == "input":
                    data = dict(attrs)
                    name = data.get("name") or ""
                    if name:
                        self.inputs[name] = data.get("value") or ""

        parser = _Parser()
        parser.feed(html)
        return parser.inputs

    def _require_credentials(self) -> tuple[str, str]:
        if not self._username or not self._password:
            raise ConfigurationError(
                "ISERV_USERNAME und ISERV_PASSWORD werden erst für geschützte Endpunkte benötigt."
            )
        return self._username, self._password

    def _raw_request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Make one request with a timeout and translate requests-level errors."""
        try:
            return self._session.request(method, url, timeout=self._timeout, **kwargs)
        except requests.Timeout as exc:
            raise TransportError(f"Zeitüberschreitung bei {method.upper()} {url}") from exc
        except requests.RequestException as exc:
            raise TransportError(
                f"Netzwerkfehler bei {method.upper()} {url}: {exc.__class__.__name__}"
            ) from exc

    def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """Retry only safe reads; never replay a potentially state-changing request."""
        method = method.upper()
        for attempt in range(self._max_retries + 1):
            try:
                response = self._raw_request(method, url, **kwargs)
            except TransportError:
                if method not in _SAFE_RETRY_METHODS or attempt >= self._max_retries:
                    raise
                time.sleep(0.2 * (2**attempt))
                continue
            if response.status_code not in _TRANSIENT_STATUSES or method not in _SAFE_RETRY_METHODS:
                return response
            if attempt >= self._max_retries:
                return response
            retry_after = response.headers.get("Retry-After")
            try:
                delay = min(max(float(retry_after), 0.0), 30.0) if retry_after else 0.2 * (2**attempt)
            except ValueError:
                delay = 0.2 * (2**attempt)
            response.close()
            time.sleep(delay)
        raise AssertionError("unreachable")

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Authenticate now instead of waiting for the first protected request."""
        self._login()

    def _login(self) -> None:
        username, password = self._require_credentials()
        resp = self._request_with_retries("GET", f"{self._iserv_base}/iserv/login", allow_redirects=True)
        if resp.status_code >= 400:
            raise AuthError(f"Login-Seite nicht erreichbar (Status {resp.status_code}).")
        post_data = self._extract_form_inputs(resp.text)
        post_data.update({"_username": username, "_password": password})
        post_resp = self._raw_request("POST", resp.url, data=post_data, allow_redirects=True)
        if post_resp.status_code >= 400:
            raise AuthError(f"Login fehlgeschlagen (Status {post_resp.status_code}). Zugangsdaten prüfen.")
        match = re.search(
            r'<meta[^>]+http-equiv=["\']refresh["\'][^>]+content=["\']0;url=([^"\']+)["\']',
            post_resp.text,
            re.IGNORECASE,
        )
        if match:
            redirect_url = urljoin(self._iserv_base, match.group(1).replace("&amp;", "&"))
            self._request_with_retries("GET", redirect_url, allow_redirects=True)
        if "IServSession" not in self._session.cookies:
            raise AuthError(f"Login fehlgeschlagen (Status {post_resp.status_code}). Zugangsdaten prüfen.")
        self._fetch_jwt()

    def _fetch_jwt(self) -> None:
        resp = self._raw_request("POST", f"{self._iserv_base}/iserv/ausleihe/session")
        if resp.status_code == 401:
            raise AuthError("Session abgelaufen. Erneuter Login erforderlich.")
        if resp.status_code >= 400:
            raise AuthError(f"JWT konnte nicht geladen werden (Status {resp.status_code}).")
        try:
            data = resp.json()
            jwt = data["jwt"]
            expiry = float(data["jwt_exp"])
        except (KeyError, TypeError, ValueError, requests.JSONDecodeError) as exc:
            raise TransportError("JWT-Antwort hat ein ungültiges Format.") from exc
        if not isinstance(jwt, str) or not jwt:
            raise TransportError("JWT-Antwort enthält kein Token.")
        self._jwt, self._jwt_exp = jwt, expiry

    def _ensure_token(self) -> None:
        if self._jwt is None:
            self._login()
        elif time.time() > self._jwt_exp - 60:
            self._fetch_jwt()

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _send(
        self,
        method: str,
        path: str,
        *,
        auth: str = "header",
        _reauth: bool = True,
        **kwargs: Any,
    ) -> requests.Response:
        method = method.upper()
        if method != "GET" and not self._allow_writes:
            raise AusleiheError(
                "Schreibende Requests (PUT/POST/DELETE) sind deaktiviert. "
                "Diese API wirkt auf die PRODUKTION — "
                "Writes nur mit AusleiheClient(allow_writes=True) und ausdrücklicher Autorisierung."
            )
        if auth not in {"header", "query", "none"}:
            raise ValueError(f"Unbekannter Auth-Modus: {auth}")
        request_kwargs = dict(kwargs)
        if auth != "none":
            self._ensure_token()
            if auth == "query":
                params = dict(request_kwargs.pop("params", {}) or {})
                params.pop("token", None)
                request_kwargs["params"] = {"token": self._jwt, **params}
            else:
                headers = dict(request_kwargs.pop("headers", {}) or {})
                headers["Authorization"] = f"Bearer {self._jwt}"
                request_kwargs["headers"] = headers
        response = self._request_with_retries(method, self._api_base + path.lstrip("/"), **request_kwargs)
        if response.status_code == 401:
            if auth != "none" and method in _SAFE_RETRY_METHODS and _reauth:
                self._jwt = None
                self._login()
                return self._send(method, path, auth=auth, _reauth=False, **kwargs)
            raise AuthError("Authentifizierung fehlgeschlagen (401).")
        if response.status_code == 403:
            raise ForbiddenError("Zugriff verweigert (403). Verwalter-Rolle benötigt.")
        if response.status_code == 404:
            raise NotFoundError(f"Nicht gefunden: {path}")
        if response.status_code >= 400:
            raise AusleiheError(f"API-Fehler {response.status_code} bei {method} {path}.")
        return response

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self._send(method, path, **kwargs)
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Any:
        return self._request("PUT", path, **kwargs)

    def _get_binary(self, path: str, **params: Any) -> bytes:
        return self._send("GET", path, auth="query", params=params).content

    @property
    def books(self) -> BookAPI:
        if self._books_api is None:
            from .books import BookAPI
            self._books_api = BookAPI(self)
        return self._books_api

    @property
    def students(self) -> StudentAPI:
        if self._students_api is None:
            from .students import StudentAPI
            self._students_api = StudentAPI(self)
        return self._students_api

    @property
    def series(self) -> SeriesAPI:
        if self._series_api is None:
            from .series import SeriesAPI
            self._series_api = SeriesAPI(self)
        return self._series_api

    @property
    def users(self) -> UserAPI:
        if self._users_api is None:
            from .users import UserAPI
            self._users_api = UserAPI(self)
        return self._users_api

    @property
    def admin(self) -> AdminAPI:
        if self._admin_api is None:
            from .admin import AdminAPI
            self._admin_api = AdminAPI(self)
        return self._admin_api

    @property
    def schoolyears(self) -> SchoolyearsAPI:
        if self._schoolyears_api is None:
            from .schoolyears import SchoolyearsAPI
            self._schoolyears_api = SchoolyearsAPI(self)
        return self._schoolyears_api

    def get_borrowing_rules(self) -> list[BorrowingRule]:
        """Public endpoint; credentials are not required."""
        response = self._send("GET", "borrowing-rules", auth="none")
        try:
            return [BorrowingRule.from_dict(data) for data in response.json()]
        except (TypeError, ValueError, requests.JSONDecodeError) as exc:
            raise TransportError("borrowing-rules lieferte kein gültiges JSON.") from exc

    def get_loan_slip_pdf(
        self,
        student_id: Optional[int] = None,
        variant: str = "student",
        start_reporting_period: Optional[str] = None,
        *,
        form_id: Optional[int] = None,
    ) -> bytes:
        if (student_id is None) == (form_id is None):
            raise ValueError("Genau einen von student_id oder form_id angeben.")
        params: dict[str, Any] = {"variant": variant}
        parameter_name = "studentId" if student_id is not None else "formId"
        params[parameter_name] = student_id if student_id is not None else form_id
        if start_reporting_period:
            params["startReportingPeriod"] = start_reporting_period
        return self._get_binary("loan-slips", **params)
