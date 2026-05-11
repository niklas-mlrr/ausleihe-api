from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AusleiheClient


class UserAPI:
    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self) -> list[dict]:
        return self._client.get("/iserv/users")

    def search_by_name(self, lastname: str = "", firstname: str = "") -> list[dict]:
        if not lastname and not firstname:
            return self.get_all()
        params: dict = {}
        if lastname:
            params["lastname"] = lastname
        if firstname:
            params["firstname"] = firstname
        return self._client.get("/iserv/users/", params=params)
