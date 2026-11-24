"""Cliente mínimo de la API pública de Crossref, sin dependencias externas."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Callable

API = "https://api.crossref.org/works"
HANDLE_API = "https://doi.org/api/handles/"

Fetch = Callable[[str], "tuple[int, bytes]"]


class CrossrefError(Exception):
    """Fallo de red o respuesta inesperada del servicio."""


@dataclass
class Work:
    """Metadatos de una obra tal como los registra Crossref."""

    doi: str
    title: str = ""
    subtitle: str = ""
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    container: str = ""
    type: str = ""

    @classmethod
    def from_message(cls, msg: dict) -> "Work":
        def first(key: str) -> str:
            value = msg.get(key) or []
            text = value[0] if isinstance(value, list) and value else ""
            return re.sub(r"<[^>]+>", "", text).strip()

        year = None
        for key in ("issued", "published-print", "published-online", "published", "created"):
            parts = (msg.get(key) or {}).get("date-parts") or [[None]]
            if parts and parts[0] and parts[0][0]:
                year = int(parts[0][0])
                break
        authors = [
            a.get("family") or a.get("name") or ""
            for a in msg.get("author") or []
        ]
        return cls(
            doi=msg.get("DOI", ""),
            title=first("title"),
            subtitle=first("subtitle"),
            authors=[a for a in authors if a],
            year=year,
            container=first("container-title"),
            type=msg.get("type", ""),
        )


class CrossrefClient:
    """Consulta Crossref por DOI o por texto bibliográfico.

    ``mailto`` identifica al usuario ante Crossref y da acceso a su servicio
    preferente (*polite pool*). ``fetch`` permite sustituir la capa de red,
    por ejemplo en las pruebas.
    """

    def __init__(
        self,
        mailto: str | None = None,
        timeout: float = 20.0,
        fetch: Fetch | None = None,
        pause: float = 0.0,
    ) -> None:
        self.mailto = mailto
        self.timeout = timeout
        self.pause = pause
        self._fetch = fetch or self._http_fetch

    def _http_fetch(self, url: str) -> tuple[int, bytes]:
        agent = "verificapa/0.2 (https://github.com/lernys/verificador-apa7_2026"
        agent += f"; mailto:{self.mailto})" if self.mailto else ")"
        request = urllib.request.Request(url, headers={"User-Agent": agent})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    return resp.status, resp.read()
            except urllib.error.HTTPError as err:
                if err.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                return err.code, err.read()
            except (urllib.error.URLError, TimeoutError, OSError) as err:
                if attempt < 2:
                    time.sleep(1 + attempt)
                    continue
                raise CrossrefError(str(err)) from err
        raise CrossrefError("sin respuesta")

    def _get_json(self, url: str) -> dict | None:
        if self.pause:
            time.sleep(self.pause)
        status, body = self._fetch(url)
        if status == 404:
            return None
        if status != 200:
            raise CrossrefError(f"HTTP {status}")
        try:
            return json.loads(body.decode("utf-8"))
        except ValueError as err:
            raise CrossrefError("respuesta no válida") from err

    def get_by_doi(self, doi: str) -> Work | None:
        """Devuelve la obra registrada con ese DOI, o ``None`` si no existe."""
        url = f"{API}/{urllib.parse.quote(doi, safe='/')}"
        if self.mailto:
            url += "?" + urllib.parse.urlencode({"mailto": self.mailto})
        data = self._get_json(url)
        if not data or "message" not in data:
            return None
        return Work.from_message(data["message"])

    def search(self, query: str, rows: int = 5) -> list[Work]:
        """Busca obras a partir del texto de una referencia."""
        params = {"query.bibliographic": query[:500], "rows": rows}
        if self.mailto:
            params["mailto"] = self.mailto
        data = self._get_json(f"{API}?{urllib.parse.urlencode(params)}")
        items = ((data or {}).get("message") or {}).get("items") or []
        return [Work.from_message(item) for item in items]

    def doi_exists(self, doi: str) -> bool:
        """Indica si el DOI está registrado en alguna agencia (no solo Crossref)."""
        url = HANDLE_API + urllib.parse.quote(doi, safe="/")
        try:
            data = self._get_json(url)
        except CrossrefError:
            return False
        return bool(data) and data.get("responseCode") == 1
