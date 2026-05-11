from __future__ import annotations

import os
import re
import time
from typing import TYPE_CHECKING, Any, Optional
from urllib.parse import quote

import requests

from .exceptions import AusleiheError, AuthError, ForbiddenError, NotFoundError

if TYPE_CHECKING:
    from .books import BookAPI
    from .series import SeriesAPI
    from .students import StudentAPI
    from .users import UserAPI


class AusleiheClient:
    def __init__(
        self,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self._domain = domain or os.environ["ISERV_DOMAIN"]
        self._username = username or os.environ["ISERV_USERNAME"]
        self._password = password or os.environ["ISERV_PASSWORD"]

        self._api_base = f"https://ausleihe-api.{self._domain}/"
        self._iserv_base = f"https://{self._domain}"
        self._frontend_origin = f"https://ausleihe.{self._domain}"

        self._session = requests.Session()
        self._session.headers.update({"Origin": self._frontend_origin})

        self._jwt: Optional[str] = None
        self._jwt_exp: float = 0.0

        # Lazy-loaded API sub-objects
        self._books_api: Optional[BookAPI] = None
        self._students_api: Optional[StudentAPI] = None
        self._series_api: Optional[SeriesAPI] = None
        self._users_api: Optional[UserAPI] = None

        # Cache for /books (18k objects, expensive to re-fetch)
        self._books_cache: Optional[tuple[list, float]] = None

        self._login()

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def _login(self) -> None:
        login_url = f"{self._iserv_base}/iserv/login"
        resp = self._session.get(login_url, allow_redirects=True)
        resp.raise_for_status()

        # Extract CSRF token from the final login form
        match = re.search(r'name="_token"\s+value="([^"]+)"', resp.text)
        if not match:
            raise AuthError("CSRF-Token nicht gefunden. Login-Seite hat unerwartetes Format.")
        csrf_token = match.group(1)

        # The _target_path must be the OAuth2 redirect URL that was the destination
        # of the redirect chain we just followed.
        target_path = resp.url.split(self._iserv_base)[-1] if self._iserv_base in resp.url else resp.url

        post_url = f"{self._iserv_base}/iserv/auth/login"
        post_resp = self._session.post(
            post_url,
            params={"_target_path": target_path},
            data={
                "_username": self._username,
                "_password": self._password,
                "_token": csrf_token,
            },
            allow_redirects=True,
        )

        # Successful login redirects through the OAuth2 code flow.
        # The session cookie IServAuthSession is now set.
        if "authentication/redirect" not in post_resp.url and post_resp.status_code not in (200, 302):
            raise AuthError(f"Login fehlgeschlagen (Status {post_resp.status_code}). Zugangsdaten prüfen.")

        self._fetch_jwt()

    def _fetch_jwt(self) -> None:
        url = f"{self._iserv_base}/iserv/ausleihe/session"
        resp = self._session.post(url)
        if resp.status_code == 401:
            raise AuthError("Session abgelaufen. Erneuter Login erforderlich.")
        resp.raise_for_status()
        data = resp.json()
        self._jwt = data["jwt"]
        self._jwt_exp = float(data["jwt_exp"])

    def _ensure_token(self) -> None:
        if time.time() > self._jwt_exp - 60:
            self._fetch_jwt()

    # ------------------------------------------------------------------
    # HTTP
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, _retry: bool = True, **kwargs: Any) -> Any:
        self._ensure_token()
        url = self._api_base + path.lstrip("/")
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._jwt}"

        resp = self._session.request(method, url, headers=headers, **kwargs)

        if resp.status_code == 401:
            if _retry:
                self._fetch_jwt()
                return self._request(method, path, _retry=False, **kwargs)
            raise AuthError("Authentifizierung fehlgeschlagen (401).")

        if resp.status_code == 403:
            raise ForbiddenError("Zugriff verweigert (403). Verwalter-Rolle benötigt.")

        if resp.status_code == 404:
            raise NotFoundError(f"Nicht gefunden: {path}")

        if resp.status_code >= 400:
            try:
                msg = resp.json()
            except Exception:
                msg = resp.text
            raise AusleiheError(f"API-Fehler {resp.status_code}: {msg}")

        return resp.json()

    def get(self, path: str, **kwargs: Any) -> Any:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Any:
        return self._request("POST", path, **kwargs)

    # ------------------------------------------------------------------
    # Sub-APIs (lazy init)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def get_borrowing_rules(self) -> list[dict]:
        """Öffentlicher Endpunkt, kein Auth nötig."""
        resp = self._session.get(f"{self._api_base}borrowing-rules")
        resp.raise_for_status()
        return resp.json()

    def get_loan_slip_pdf(
        self,
        student_id: int,
        variant: str = "student",
        start_reporting_period: Optional[str] = None,
        doublepage: bool = False,
    ) -> bytes:
        """Leihschein als PDF (gibt rohe Bytes zurück)."""
        self._ensure_token()
        params: dict[str, Any] = {
            "token": self._jwt,
            "studentId": student_id,
            "variant": variant,
        }
        if start_reporting_period:
            params["startReportingPeriod"] = start_reporting_period
        if doublepage:
            params["doublepage"] = "true"
        resp = self._session.get(f"{self._api_base}loan-slips", params=params)
        resp.raise_for_status()
        return resp.content
