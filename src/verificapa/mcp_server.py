"""Servidor MCP de verificapa.

Permite que Claude y otros asistentes compatibles con MCP verifiquen
referencias durante una conversación. Se arranca con ``verificapa-mcp`` y
necesita el extra ``mcp``: ``pip install "verificapa[mcp]"``.
"""

from __future__ import annotations

import os

from .cli import render_markdown
from .crossref import CrossrefClient, CrossrefError
from .parser import DOI_RE, clean_doi, parse_reference
from .verifier import title_similarity, verify_text

MAX_REFERENCES = 100

INSTRUCTIONS = (
    "Verifica referencias bibliográficas (APA 7) contra Crossref. Úsalo cuando "
    "haya que comprobar si las referencias de un trabajo existen, detectar citas "
    "inventadas por una IA, encontrar un DOI que falta o revisar el formato APA 7. "
    "«No encontrada» no equivale a «inventada»: libros, informes y muchas revistas "
    "no están en Crossref. Presenta los resultados como indicios que revisar, "
    "nunca como prueba de fraude."
)


def _client() -> CrossrefClient:
    return CrossrefClient(mailto=os.environ.get("VERIFICAPA_MAILTO"), pause=0.1)


def verificar_referencias(referencias: str, idioma: str = "es", solo_formato: bool = False) -> str:
    """Verifica una lista de referencias APA 7 y devuelve un informe en Markdown.

    Comprueba cada referencia en Crossref: si el DOI existe, si pertenece a esa
    obra y si coinciden autor y año. Para las referencias sin DOI busca la obra
    y sugiere su DOI. También avisa de descuidos de formato APA 7.

    Args:
        referencias: Texto con las referencias, una por párrafo o una por línea.
        idioma: Idioma del informe, "es" o "en".
        solo_formato: Si es verdadero, revisa solo el formato y no consulta Crossref.
    """
    lang = "en" if idioma == "en" else "es"
    client = None if solo_formato else _client()
    results = verify_text(referencias, client, offline=solo_formato)
    if len(results) > MAX_REFERENCES:
        return (
            f"Hay {len(results)} referencias y el máximo por llamada es {MAX_REFERENCES}. "
            "Divida la lista en varias partes."
        )
    return render_markdown(results, lang)


def consultar_doi(doi: str) -> str:
    """Indica si un DOI existe y a qué obra pertenece según Crossref.

    Args:
        doi: El DOI, con o sin el prefijo https://doi.org/.
    """
    match = DOI_RE.search(doi)
    if not match:
        return f"«{doi}» no tiene forma de DOI. Un DOI empieza por 10. y lleva una barra."
    doi = clean_doi(match.group(0))
    client = _client()
    try:
        work = client.get_by_doi(doi)
        if work is None:
            if client.doi_exists(doi):
                return (
                    f"El DOI {doi} existe, pero lo gestiona otra agencia (DataCite, mEDRA…). "
                    "Crossref no tiene sus datos."
                )
            return f"El DOI {doi} no está registrado en ninguna agencia."
    except CrossrefError as err:
        return f"No se pudo consultar Crossref: {err}"
    authors = ", ".join(work.authors[:10]) or "sin autores registrados"
    return (
        f"**{work.title}**\n\n"
        f"- Autores: {authors}\n"
        f"- Año: {work.year or 'desconocido'}\n"
        f"- Publicación: {work.container or 'no consta'}\n"
        f"- Tipo: {work.type or 'no consta'}\n"
        f"- DOI: https://doi.org/{work.doi}"
    )


def buscar_obra(referencia: str, resultados: int = 3) -> str:
    """Busca en Crossref las obras que más se parecen a una referencia o un título.

    Sirve para encontrar el DOI que falta o para comprobar una referencia dudosa.

    Args:
        referencia: La referencia completa o solo el título de la obra.
        resultados: Número de candidatas que se devuelven, de 1 a 10.
    """
    rows = max(1, min(int(resultados), 10))
    ref = parse_reference(referencia)
    if ref.title is None:
        ref.title = referencia
    try:
        works = _client().search(referencia, rows=rows)
    except CrossrefError as err:
        return f"No se pudo consultar Crossref: {err}"
    if not works:
        return "Crossref no devuelve ninguna obra parecida."
    lines = []
    for work in works:
        sim = round(title_similarity(ref, work) * 100)
        authors = ", ".join(work.authors[:3]) + (" et al." if len(work.authors) > 3 else "")
        lines.append(
            f"- **{work.title}** ({work.year or 's. f.'}). {authors}. {work.container}. "
            f"https://doi.org/{work.doi} · parecido del título: {sim} %"
        )
    return "\n".join(lines)


def build_server():
    """Crea el servidor MCP. Admite las versiones 1 y 2 del SDK de Python."""
    try:
        from mcp.server.mcpserver import MCPServer as Server  # SDK 2.x
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP as Server  # SDK 1.x
        except ImportError as err:
            raise SystemExit(
                'Falta el SDK de MCP. Instálelo con: pip install "verificapa[mcp]"'
            ) from err
    from mcp.types import ToolAnnotations

    server = Server("verificapa", instructions=INSTRUCTIONS)
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=True)
    for tool in (verificar_referencias, consultar_doi, buscar_obra):
        server.tool(annotations=read_only)(tool)
    return server


def main() -> None:
    build_server().run()


if __name__ == "__main__":
    main()
