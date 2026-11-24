"""Comprobaciones de formato APA 7 que no necesitan conexión.

Solo se incluyen reglas con poco riesgo de falso aviso. No sustituyen la
revisión de quien escribe: detectan los descuidos más frecuentes.
"""

from __future__ import annotations

import re

from .parser import DOI_RE, Reference

_DOI_OK_RE = re.compile(r"https://doi\.org/10\.\d{4,9}/", re.IGNORECASE)
_RETRIEVED_RE = re.compile(
    r"(recuperado de|retrieved from|disponible en|available at)\s*:?\s*https?://",
    re.IGNORECASE,
)
_ET_AL_RE = re.compile(r"\bet\s+al\b\.?", re.IGNORECASE)
_LINK_END_RE = re.compile(r"(https?://\S+|10\.\d{4,9}/\S+)\.$", re.IGNORECASE)


def check_format(ref: Reference, conjunction: str | None = None) -> list[tuple[str, dict]]:
    """Devuelve los avisos de formato como pares ``(código, parámetros)``.

    ``conjunction`` puede ser ``"y"`` o ``"&"`` para exigir una de las dos
    formas ante el último autor. Por defecto no se comprueba.
    """
    issues: list[tuple[str, dict]] = []
    raw = ref.raw.strip()

    if ref.year is None:
        issues.append(("no_year", {}))

    if DOI_RE.search(raw) and not _DOI_OK_RE.search(raw):
        issues.append(("doi_format", {"doi": ref.doi or ""}))

    if _LINK_END_RE.search(raw):
        issues.append(("period_after_link", {}))

    if _RETRIEVED_RE.search(raw):
        issues.append(("retrieved_from", {}))

    year_pos = raw.find("(")
    author_part = raw[:year_pos] if year_pos > 0 else raw
    if _ET_AL_RE.search(author_part):
        issues.append(("et_al", {}))

    if conjunction == "y" and "&" in author_part:
        issues.append(("conjunction", {"expected": "y", "found": "&"}))
    elif conjunction == "&" and re.search(r"\.,?\s+(y|e)\s+[^\W\d_]", author_part):
        issues.append(("conjunction", {"expected": "&", "found": "y"}))

    return issues
