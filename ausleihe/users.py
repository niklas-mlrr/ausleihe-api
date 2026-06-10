from __future__ import annotations

from typing import TYPE_CHECKING

from ._util import name_params

if TYPE_CHECKING:
    from .client import AusleiheClient


class UserAPI:
    """IServ-Nutzer (Lehrer + Schüler + Verwalter).

    Hinweis: Gibt bewusst rohe ``dict``s zurück (kein ``User``-Dataclass-Modell),
    anders als ``StudentAPI``, das ``Student``-Objekte liefert. Der ``/iserv/users``-
    Payload ist nicht modelliert; bei Bedarf direkt auf den dict-Feldern arbeiten.
    """

    def __init__(self, client: AusleiheClient) -> None:
        self._client = client

    def get_all(self) -> list[dict]:
        return self._client.get("/iserv/users")

    def search_by_name(self, lastname: str = "", firstname: str = "") -> list[dict]:
        if not lastname and not firstname:
            return self.get_all()
        return self._client.get("/iserv/users/", params=name_params(lastname, firstname))
