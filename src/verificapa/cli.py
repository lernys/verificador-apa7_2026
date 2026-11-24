"""Interfaz de línea de órdenes: ``verificapa referencias.txt``."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from . import __version__
from .crossref import CrossrefClient
from .messages import EXPLAIN, LABELS, STATUS, issue_text
from .verifier import PROBLEM_STATUSES, Result, verify_text


def _work_line(result: Result) -> str:
    work = result.work
    if work is None:
        return ""
    authors = ", ".join(work.authors[:3]) + (" et al." if len(work.authors) > 3 else "")
    year = f"({work.year})" if work.year else ""
    head = " ".join(p for p in (authors, year) if p)
    body = [p for p in (head, work.title, work.container) if p]
    return ". ".join(body) + f". https://doi.org/{work.doi}"


def _summary(results: list[Result], lang: str) -> str:
    counts = Counter(r.status.value for r in results)
    parts = [f"{len(results)} {LABELS[lang]['references']}"]
    parts += [f"{n} {STATUS[lang][s][1].lower()}" for s, n in counts.items()]
    return f"{LABELS[lang]['summary']}: " + " | ".join(parts)


def render_text(results: list[Result], lang: str = "es") -> str:
    if not results:
        return LABELS[lang]["none"]
    lines: list[str] = []
    for r in results:
        symbol, label = STATUS[lang][r.status.value]
        lines.append(f"[{r.index}] {symbol} {label.upper()}")
        lines.append(f"    {r.reference.raw}")
        if r.status.value in EXPLAIN[lang]:
            lines.append(f"    → {EXPLAIN[lang][r.status.value]}")
        if r.work is not None:
            lines.append(f"    {LABELS[lang]['crossref']}: {_work_line(r)}")
        if r.suggested_doi:
            lines.append(f"    {LABELS[lang]['suggested']}: https://doi.org/{r.suggested_doi}")
        for issue in r.issues:
            lines.append(f"    • {issue_text(issue.code, issue.params, lang)}")
        lines.append("")
    lines.append(_summary(results, lang))
    return "\n".join(lines)


def render_markdown(results: list[Result], lang: str = "es") -> str:
    if not results:
        return LABELS[lang]["none"]
    lines = [f"# {LABELS[lang]['title']}", "", _summary(results, lang), ""]
    for r in results:
        symbol, label = STATUS[lang][r.status.value]
        lines += [f"## {r.index}. {symbol} {label}", "", f"> {r.reference.raw}", ""]
        if r.status.value in EXPLAIN[lang]:
            lines += [EXPLAIN[lang][r.status.value], ""]
        if r.work is not None:
            lines.append(f"- **{LABELS[lang]['crossref']}:** {_work_line(r)}")
        if r.suggested_doi:
            lines.append(f"- **{LABELS[lang]['suggested']}:** https://doi.org/{r.suggested_doi}")
        lines += [f"- {issue_text(i.code, i.params, lang)}" for i in r.issues]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(results: list[Result]) -> str:
    return json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verificapa",
        description="Verifica referencias APA 7 contra Crossref y detecta citas inventadas. "
        "Verifies APA 7 references against Crossref and flags fabricated citations.",
    )
    parser.add_argument("file", help="archivo de texto con las referencias, o «-» para la entrada estándar")
    parser.add_argument("-f", "--format", choices=("text", "json", "markdown"), default="text", help="formato de salida")
    parser.add_argument("-l", "--lang", choices=("es", "en"), default="es", help="idioma del informe")
    parser.add_argument("--mailto", help="su correo, para el servicio preferente de Crossref")
    parser.add_argument("--conjunction", choices=("y", "&"), help="exige «y» o «&» ante el último autor")
    parser.add_argument("--offline", action="store_true", help="solo revisa el formato, sin conexión")
    parser.add_argument("--strict", action="store_true", help="termina con código 1 si hay referencias dudosas")
    parser.add_argument("-o", "--output", help="guarda el informe en un archivo")
    parser.add_argument("--version", action="version", version=f"verificapa {__version__}")
    return parser


def main(argv: list[str] | None = None, client: CrossrefClient | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.file == "-":
        text = sys.stdin.read()
    else:
        try:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as err:
            print(f"verificapa: {err}", file=sys.stderr)
            return 2

    if client is None and not args.offline:
        client = CrossrefClient(mailto=args.mailto, pause=0.1)
    results = verify_text(text, client, conjunction=args.conjunction, offline=args.offline)

    if args.format == "json":
        report = render_json(results)
    elif args.format == "markdown":
        report = render_markdown(results, args.lang)
    else:
        report = render_text(results, args.lang)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(report + "\n")
    else:
        print(report)

    if args.strict and any(r.status in PROBLEM_STATUSES for r in results):
        return 1
    return 0
