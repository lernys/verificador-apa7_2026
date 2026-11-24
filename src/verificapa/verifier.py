"""Contrasta cada referencia con Crossref y decide su estado."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum

from .crossref import CrossrefClient, CrossrefError, Work
from .formato import check_format
from .parser import DOI_RE, URL_RE, Reference, parse_reference, split_references


class Status(str, Enum):
    VERIFIED = "verified"  # el DOI existe y los datos coinciden
    FOUND = "found"  # sin DOI en la referencia, pero la obra existe
    REVIEW = "review"  # coincidencia parcial: conviene revisarla a mano
    MISMATCH = "mismatch"  # el DOI existe, pero es de otra obra
    DOI_NOT_FOUND = "doi_not_found"  # el DOI no está registrado
    NOT_FOUND = "not_found"  # no aparece en Crossref
    OTHER_AGENCY = "other_agency"  # DOI válido de otra agencia (DataCite…)
    ERROR = "error"  # no se pudo consultar el servicio
    FORMAT_ONLY = "format_only"  # modo sin conexión


PROBLEM_STATUSES = {Status.MISMATCH, Status.DOI_NOT_FOUND, Status.NOT_FOUND}


@dataclass
class Issue:
    code: str
    params: dict = field(default_factory=dict)
    kind: str = "format"  # "format" o "data"


@dataclass
class Result:
    index: int
    reference: Reference
    status: Status
    work: Work | None = None
    title_similarity: float | None = None
    suggested_doi: str | None = None
    issues: list[Issue] = field(default_factory=list)

    def to_dict(self) -> dict:
        ref, work = self.reference, self.work
        return {
            "index": self.index,
            "status": self.status.value,
            "reference": {
                "raw": ref.raw,
                "authors": ref.authors,
                "year": ref.year,
                "title": ref.title,
                "container": ref.container,
                "doi": ref.doi,
            },
            "crossref": None
            if work is None
            else {
                "doi": work.doi,
                "title": work.title,
                "authors": work.authors,
                "year": work.year,
                "container": work.container,
                "type": work.type,
            },
            "title_similarity": None
            if self.title_similarity is None
            else round(self.title_similarity, 3),
            "suggested_doi": self.suggested_doi,
            "issues": [
                {"code": i.code, "kind": i.kind, "params": i.params} for i in self.issues
            ],
        }


def normalize(text: str) -> str:
    """Minúsculas, sin acentos ni puntuación, espacios simples."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[^\w\s]", " ", text.lower()).replace("_", " ")
    return " ".join(text.split())


def title_similarity(ref: Reference, work: Work) -> float:
    """Parecido entre el título de la referencia y el de Crossref (0 a 1)."""
    candidates = [work.title]
    if work.subtitle:
        candidates.append(f"{work.title} {work.subtitle}")
    raw = normalize(ref.raw)
    title = normalize(ref.title or "")
    best = 0.0
    for candidate in candidates:
        cand = normalize(candidate)
        if not cand:
            continue
        if len(cand) >= 15 and cand in raw:
            return 1.0
        if title:
            best = max(best, SequenceMatcher(None, title, cand).ratio())
    return best


def author_matches(ref: Reference, work: Work) -> bool | None:
    """Comprueba el primer autor. ``None`` si falta el dato en algún lado."""
    if not ref.authors or not work.authors:
        return None
    mine = normalize(ref.authors[0]).replace(" ", "")
    if not mine:
        return None
    for family in work.authors:
        theirs = normalize(family).replace(" ", "")
        if not theirs:
            continue
        if mine == theirs:
            return True
        # Apellidos compuestos: «García» frente a «García-Peñalvo».
        short, long_ = sorted((mine, theirs), key=len)
        if len(short) >= 4 and (long_.startswith(short) or long_.endswith(short)):
            return True
    return False


def _compare(ref: Reference, work: Work) -> tuple[float, bool | None, list[Issue]]:
    issues: list[Issue] = []
    sim = title_similarity(ref, work)
    author_ok = author_matches(ref, work)
    if author_ok is False:
        issues.append(
            Issue(
                "author_mismatch",
                {"reference": ref.authors[0], "crossref": ", ".join(work.authors[:3])},
                "data",
            )
        )
    if ref.year and ref.year.isdigit() and work.year:
        diff = abs(int(ref.year) - work.year)
        if diff > 1:
            issues.append(
                Issue("year_mismatch", {"reference": ref.year, "crossref": work.year}, "data")
            )
        elif diff == 1:
            issues.append(
                Issue("year_close", {"reference": ref.year, "crossref": work.year}, "data")
            )
    return sim, author_ok, issues


def _search(ref: Reference, client: CrossrefClient) -> tuple[Work | None, float, bool | None, list[Issue]]:
    query = URL_RE.sub("", DOI_RE.sub("", ref.raw)).strip()
    best: tuple[Work | None, float, bool | None, list[Issue]] = (None, 0.0, None, [])
    best_score = -1.0
    for work in client.search(query):
        sim, author_ok, issues = _compare(ref, work)
        score = sim + (0.1 if author_ok else 0.0)
        if score > best_score:
            best_score = score
            best = (work, sim, author_ok, issues)
    return best


def verify_reference(
    raw: str,
    client: CrossrefClient | None = None,
    index: int = 1,
    conjunction: str | None = None,
    offline: bool = False,
) -> Result:
    """Verifica una referencia y devuelve su resultado."""
    ref = parse_reference(raw)
    format_issues = [Issue(code, params, "format") for code, params in check_format(ref, conjunction)]
    result = Result(index=index, reference=ref, status=Status.FORMAT_ONLY, issues=format_issues)
    if offline:
        return result
    client = client or CrossrefClient()

    try:
        if ref.doi:
            work = client.get_by_doi(ref.doi)
            if work is not None:
                sim, author_ok, issues = _compare(ref, work)
                result.work, result.title_similarity = work, sim
                if sim >= 0.8:
                    result.status = Status.REVIEW if author_ok is False else Status.VERIFIED
                    result.issues += issues
                elif sim >= 0.5:
                    result.status = Status.REVIEW
                    result.issues += issues
                else:
                    result.status = Status.MISMATCH
                return result
            if client.doi_exists(ref.doi):
                result.status = Status.OTHER_AGENCY
                return result
            result.status = Status.DOI_NOT_FOUND
            work, sim, author_ok, _ = _search(ref, client)
            if work is not None and sim >= 0.9 and author_ok is not False:
                result.work, result.title_similarity = work, sim
                result.suggested_doi = work.doi
            return result

        work, sim, author_ok, issues = _search(ref, client)
        if work is not None and sim >= 0.9 and author_ok is not False:
            result.status = Status.FOUND
            result.work, result.title_similarity = work, sim
            result.suggested_doi = work.doi
            result.issues += issues
        elif work is not None and sim >= 0.75:
            result.status = Status.REVIEW
            result.work, result.title_similarity = work, sim
            result.issues += issues
        else:
            result.status = Status.NOT_FOUND
        return result
    except CrossrefError as err:
        result.status = Status.ERROR
        result.issues.append(Issue("network_error", {"detail": str(err)}, "data"))
        return result


def verify_text(
    text: str,
    client: CrossrefClient | None = None,
    conjunction: str | None = None,
    offline: bool = False,
) -> list[Result]:
    """Verifica todas las referencias contenidas en un texto."""
    client = client or (None if offline else CrossrefClient())
    return [
        verify_reference(raw, client, index=i, conjunction=conjunction, offline=offline)
        for i, raw in enumerate(split_references(text), start=1)
    ]
