"""verificapa: verifica referencias APA 7 contra Crossref y detecta citas inventadas."""

from .crossref import CrossrefClient, CrossrefError, Work
from .formato import check_format
from .parser import Reference, parse_reference, split_references
from .verifier import Issue, Result, Status, verify_reference, verify_text

__version__ = "0.2.0"

__all__ = [
    "CrossrefClient",
    "CrossrefError",
    "Issue",
    "Reference",
    "Result",
    "Status",
    "Work",
    "check_format",
    "parse_reference",
    "split_references",
    "verify_reference",
    "verify_text",
]
