"""Crossref simulado: las pruebas no necesitan conexión."""

import json
import urllib.parse

import pytest

from verificapa import CrossrefClient

DEEP_LEARNING = {
    "DOI": "10.1038/nature14539",
    "title": ["Deep learning"],
    "author": [{"family": "LeCun"}, {"family": "Bengio"}, {"family": "Hinton"}],
    "issued": {"date-parts": [[2015, 5, 27]]},
    "container-title": ["Nature"],
    "type": "journal-article",
}
GPT3 = {
    "DOI": "10.1007/s11023-020-09548-1",
    "title": ["GPT-3: Its Nature, Scope, Limits, and Consequences"],
    "author": [{"family": "Floridi"}, {"family": "Chiriatti"}],
    "issued": {"date-parts": [[2020, 11, 1]]},
    "container-title": ["Minds and Machines"],
    "type": "journal-article",
}
UNRELATED = {
    "DOI": "10.1234/unrelated",
    "title": ["A study of soil bacteria in alpine meadows"],
    "author": [{"family": "Meier"}],
    "issued": {"date-parts": [[2011]]},
    "container-title": ["Soil Journal"],
    "type": "journal-article",
}
BY_DOI = {w["DOI"]: w for w in (DEEP_LEARNING, GPT3, UNRELATED)}
OTHER_AGENCY = {"10.48550/arxiv.1706.03762"}


def fake_fetch(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc == "doi.org":
        doi = urllib.parse.unquote(parsed.path.split("/api/handles/")[1]).lower()
        known = doi in OTHER_AGENCY or doi in BY_DOI
        code = 1 if known else 100
        return (200 if known else 404), json.dumps({"responseCode": code}).encode()
    path = urllib.parse.unquote(parsed.path)
    if path.rstrip("/") == "/works":
        query = urllib.parse.parse_qs(parsed.query)["query.bibliographic"][0].lower()
        if "gpt-3" in query:
            items = [UNRELATED, GPT3]
        elif "deep learning" in query and "lecun" in query:
            items = [DEEP_LEARNING]
        else:
            items = [UNRELATED]
        return 200, json.dumps({"message": {"items": items}}).encode()
    doi = path.split("/works/")[1]
    if doi in BY_DOI:
        return 200, json.dumps({"message": BY_DOI[doi]}).encode()
    return 404, b"Resource not found."


@pytest.fixture
def client():
    return CrossrefClient(fetch=fake_fetch)
