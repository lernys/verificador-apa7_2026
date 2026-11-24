"""Separa una lista de referencias y extrae sus campos básicos.

El análisis es heurístico: APA 7 admite muchas variantes y no se pretende
cubrirlas todas. Basta con obtener autores, año, título y DOI con la
fiabilidad suficiente para buscar la obra en Crossref.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DOI_RE = re.compile(r'10\.\d{4,9}/[^\s"<>]+', re.IGNORECASE)
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
YEAR_RE = re.compile(
    r"\(\s*(?:((?:1[5-9]|20)\d{2})[a-z]?(?:\s*,[^)]*)?"
    r"|(s\.\s?f\.|n\.\s?d\.|en prensa|in press))\s*\)",
    re.IGNORECASE,
)
_HEADING_RE = re.compile(
    r"^(referencias|references|bibliograf[ií]a|bibliography|"
    r"referencias bibliogr[aá]ficas|obras citadas)\s*:?$",
    re.IGNORECASE,
)
_BULLET_RE = re.compile(r"^(?:[-*•]\s+|\[?\d{1,3}[\].)]\s+)")
_SURNAME_RE = re.compile(r"([^\W\d_][^,.&;()]*?),\s*(?:[^\W\d_]\.[\s\-]*)+")
_CONJ_RE = re.compile(r"^(?:y|e|and|&|\.\.\.|…)\s+", re.IGNORECASE)
_TITLE_END_RE = re.compile(r"(?<=[.?!])\s+(?=[A-ZÁÉÍÓÚÑÜ¿¡\"«“\d(])")


@dataclass
class Reference:
    """Una referencia bibliográfica y los campos que se han podido extraer."""

    raw: str
    authors: list[str] = field(default_factory=list)
    year: str | None = None
    title: str | None = None
    container: str | None = None
    doi: str | None = None
    url: str | None = None


def clean_doi(doi: str) -> str:
    """Quita la puntuación final que no pertenece al DOI."""
    doi = doi.rstrip(".,;]>")
    while doi.endswith(")") and doi.count("(") < doi.count(")"):
        doi = doi[:-1].rstrip(".,;")
    return doi


def split_references(text: str) -> list[str]:
    """Divide un texto en referencias individuales.

    Admite referencias separadas por líneas en blanco, una por línea, o con
    líneas partidas dentro de un mismo párrafo.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    refs: list[str] = []
    for block in re.split(r"\n\s*\n", text.strip()):
        current = ""
        for line in block.split("\n"):
            line = _BULLET_RE.sub("", line.strip())
            if not line or _HEADING_RE.match(line):
                continue
            starts_new = bool(YEAR_RE.search(line[:300])) and bool(YEAR_RE.search(current))
            if current and starts_new:
                refs.append(current)
                current = line
            else:
                current = f"{current} {line}".strip()
        if current:
            refs.append(current)
    return [" ".join(r.split()) for r in refs]


def _plain(text: str) -> str:
    """Elimina las marcas de cursiva de Markdown."""
    return re.sub(r"(?<!\w)[*_]+|[*_]+(?!\w)", "", text)


def parse_reference(raw: str) -> Reference:
    """Extrae autores, año, título, publicación y DOI de una referencia."""
    ref = Reference(raw=raw)
    text = _plain(raw)

    doi_match = DOI_RE.search(text)
    if doi_match:
        ref.doi = clean_doi(doi_match.group(0))
    url_match = URL_RE.search(text)
    if url_match:
        ref.url = url_match.group(0).rstrip(".,;")

    year_match = YEAR_RE.search(text)
    if not year_match:
        return ref
    ref.year = year_match.group(1) or year_match.group(2)

    before = text[: year_match.start()].strip().rstrip(".").strip()
    surnames = [_CONJ_RE.sub("", s).strip() for s in _SURNAME_RE.findall(before + ".")]
    surnames = [s for s in surnames if s]
    if surnames:
        ref.authors = surnames
    elif before:
        ref.authors = [before]

    after = text[year_match.end() :].lstrip(". ").strip()
    cut = len(after)
    for pattern in (URL_RE, DOI_RE, re.compile(r"\bdoi\s*:", re.IGNORECASE)):
        found = pattern.search(after)
        if found:
            cut = min(cut, found.start())
    after = after[:cut].strip()
    if not after:
        return ref

    parts = _TITLE_END_RE.split(after, maxsplit=1)
    ref.title = parts[0].strip().rstrip(".").strip() or None
    if len(parts) > 1:
        container = re.split(r",|\.\s", parts[1], maxsplit=1)[0].strip().rstrip(".")
        ref.container = container or None
    return ref
