"""Textos de salida en español e inglés."""

from __future__ import annotations

STATUS = {
    "es": {
        "verified": ("✔", "Verificada"),
        "found": ("✔", "Encontrada (falta el DOI)"),
        "review": ("?", "Revisar a mano"),
        "mismatch": ("✘", "El DOI es de otra obra"),
        "doi_not_found": ("✘", "El DOI no existe"),
        "not_found": ("✘", "No encontrada en Crossref"),
        "other_agency": ("~", "DOI válido, fuera de Crossref"),
        "error": ("!", "No se pudo comprobar"),
        "format_only": ("·", "Solo formato"),
    },
    "en": {
        "verified": ("✔", "Verified"),
        "found": ("✔", "Found (DOI missing)"),
        "review": ("?", "Review by hand"),
        "mismatch": ("✘", "DOI belongs to another work"),
        "doi_not_found": ("✘", "DOI does not exist"),
        "not_found": ("✘", "Not found in Crossref"),
        "other_agency": ("~", "Valid DOI, outside Crossref"),
        "error": ("!", "Could not be checked"),
        "format_only": ("·", "Format only"),
    },
}

EXPLAIN = {
    "es": {
        "mismatch": "El DOI existe, pero Crossref lo asigna a esta otra obra. Es el patrón típico de una referencia inventada.",
        "doi_not_found": "Ninguna agencia tiene registrado este DOI. Puede estar mal copiado o ser inventado.",
        "not_found": "Crossref no tiene ninguna obra parecida. Puede ser inventada, pero también un libro, un informe o una revista sin DOI. Compruébela en otra fuente.",
        "other_agency": "El DOI existe, pero lo gestiona otra agencia (DataCite, mEDRA…). No se pueden comparar los datos.",
        "review": "La coincidencia es parcial. Compare la referencia con el registro de Crossref.",
    },
    "en": {
        "mismatch": "The DOI exists, but Crossref assigns it to this other work. This is the typical pattern of a fabricated reference.",
        "doi_not_found": "No agency has this DOI on record. It may be miscopied or fabricated.",
        "not_found": "Crossref has no similar work. It may be fabricated, but it may also be a book, a report or a journal without DOIs. Check it in another source.",
        "other_agency": "The DOI exists, but another agency manages it (DataCite, mEDRA…). The data cannot be compared.",
        "review": "The match is partial. Compare the reference with the Crossref record.",
    },
}

ISSUES = {
    "es": {
        "no_year": "No se encuentra el año entre paréntesis tras los autores.",
        "doi_format": "El DOI debe escribirse como enlace: https://doi.org/{doi}",
        "period_after_link": "No se pone punto final después de un DOI o una URL.",
        "retrieved_from": "APA 7 ya no usa «Recuperado de» ante la URL, salvo que haga falta la fecha de consulta.",
        "et_al": "En la lista de referencias no se usa «et al.»: se escriben hasta 20 autores.",
        "conjunction": "Se esperaba «{expected}» ante el último autor y aparece «{found}».",
        "author_mismatch": "El primer autor no coincide: la referencia dice «{reference}» y Crossref, «{crossref}».",
        "year_mismatch": "El año no coincide: la referencia dice {reference} y Crossref, {crossref}.",
        "year_close": "El año difiere en uno ({reference} frente a {crossref}). Suele deberse a la publicación anticipada en línea.",
        "network_error": "Error de conexión: {detail}",
    },
    "en": {
        "no_year": "No year in parentheses was found after the authors.",
        "doi_format": "The DOI must be written as a link: https://doi.org/{doi}",
        "period_after_link": "Do not put a period after a DOI or URL.",
        "retrieved_from": "APA 7 no longer uses “Retrieved from” before the URL, unless a retrieval date is needed.",
        "et_al": "Do not use “et al.” in the reference list: write up to 20 authors.",
        "conjunction": "Expected “{expected}” before the last author, found “{found}”.",
        "author_mismatch": "First author differs: the reference says “{reference}”, Crossref says “{crossref}”.",
        "year_mismatch": "Year differs: the reference says {reference}, Crossref says {crossref}.",
        "year_close": "Year differs by one ({reference} vs {crossref}). This is usually due to online-first publication.",
        "network_error": "Connection error: {detail}",
    },
}

LABELS = {
    "es": {
        "crossref": "Crossref",
        "suggested": "DOI sugerido",
        "summary": "Resumen",
        "references": "referencias",
        "none": "No se han encontrado referencias en el texto.",
        "title": "Informe de verificación de referencias",
    },
    "en": {
        "crossref": "Crossref",
        "suggested": "Suggested DOI",
        "summary": "Summary",
        "references": "references",
        "none": "No references were found in the text.",
        "title": "Reference verification report",
    },
}


def issue_text(code: str, params: dict, lang: str) -> str:
    template = ISSUES[lang].get(code, code)
    try:
        return template.format(**params)
    except (KeyError, IndexError):
        return template
