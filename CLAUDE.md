# IServ Ausleihe API — Project Memory

Inoffizieller Python-Wrapper für die IServ Schulbuchausleihe REST API
(reverse-engineered). Vollständige Doku im Wiki:
`~/cc/wiki/30_projects/sba/ausleihe_api/` (overview, auth, api_reference, schemas,
write_endpoints).

## ⚠️ PRODUKTIONS-SCHUTZ — UNBEDINGT BEACHTEN

Die `.env` enthält **echte IServ-Zugangsdaten gegen die PRODUKTIONSUMGEBUNG** der
Schule. Diese Credentials greifen auf reale, produktive Schul-/Schülerdaten zu.

**ABSOLUTE REGELN:**

- **NIEMALS** die `.env`-Credentials nutzen, um die Produktionsumgebung zu
  verändern (kein Tampering).
- **NUR GET / Lesezugriff ist erlaubt.** Keine Daten ändern, anlegen oder löschen.
- **KEINE** schreibenden Requests gegen Produktion: kein **PUT**, **POST**,
  **DELETE** oder sonstiger State-ändernder Aufruf — auch nicht „zum Testen".
- Die in [Write Endpoints](../../../cc/wiki/30_projects/sba/ausleihe_api/write_endpoints.md)
  dokumentierten Schreib-Endpunkte sind **rein zur Dokumentation** erfasst, nicht
  zur Ausführung.
- Die Library bewusst **read-only** halten (nur `client.get`). Write-Wrapper nur
  anlegen, wenn zwingend nötig — und selbst dann nie ungeprüft gegen Produktion
  ausführen.
- Im Zweifel: **nicht ausführen, erst nachfragen.** Mit Produktions-Credentials
  extrem vorsichtig umgehen; niemals committen oder loggen.

GET / Lesen ist okay. Alles andere gegen Produktion ist tabu.
