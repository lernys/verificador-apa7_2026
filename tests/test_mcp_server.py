import asyncio
import sys

import pytest

from verificapa import mcp_server


@pytest.fixture(autouse=True)
def crossref_simulado(client, monkeypatch):
    monkeypatch.setattr(mcp_server, "_client", lambda: client)


def test_verificar_referencias_devuelve_informe():
    informe = mcp_server.verificar_referencias(
        "LeCun, Y., Bengio, Y. y Hinton, G. (2015). Deep learning. Nature. "
        "https://doi.org/10.1038/nature14539\n\n"
        "Ruiz, A. (2022). Obra fantasma. Revista. https://doi.org/10.9999/nada"
    )
    assert "Verificada" in informe and "El DOI no existe" in informe


def test_verificar_referencias_en_ingles_y_solo_formato():
    informe = mcp_server.verificar_referencias("A, B. (2020). T. R. doi:10.1000/x", "en", True)
    assert "Format only" in informe and "must be written as a link" in informe


def test_consultar_doi():
    assert "Deep learning" in mcp_server.consultar_doi("https://doi.org/10.1038/nature14539")
    assert "no está registrado" in mcp_server.consultar_doi("10.9999/nada")
    assert "otra agencia" in mcp_server.consultar_doi("10.48550/arXiv.1706.03762")
    assert "no tiene forma de DOI" in mcp_server.consultar_doi("hola")


def test_buscar_obra():
    salida = mcp_server.buscar_obra("GPT-3: Its nature, scope, limits, and consequences")
    assert "10.1007/s11023-020-09548-1" in salida and "100 %" in salida


def test_servidor_por_stdio():
    """Arranca el servidor de verdad y llama a una herramienta sin usar la red."""
    pytest.importorskip("mcp")
    from mcp import ClientSession, StdioServerParameters, stdio_client

    async def run():
        params = StdioServerParameters(command=sys.executable, args=["-m", "verificapa.mcp_server"])
        async with stdio_client(params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools = {t.name for t in (await session.list_tools()).tools}
                result = await session.call_tool(
                    "verificar_referencias",
                    {"referencias": "A, B. (2020). T. R. doi:10.1000/x", "solo_formato": True},
                )
                return tools, result.content[0].text

    tools, text = asyncio.run(run())
    assert tools == {"verificar_referencias", "consultar_doi", "buscar_obra"}
    assert "Solo formato" in text
