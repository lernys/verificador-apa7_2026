import json

from verificapa import CrossrefClient, CrossrefError, Status, verify_reference, verify_text
from verificapa.cli import main


def test_doi_correcto(client):
    r = verify_reference(
        "LeCun, Y., Bengio, Y. y Hinton, G. (2015). Deep learning. Nature, 521(7553), "
        "436-444. https://doi.org/10.1038/nature14539",
        client,
    )
    assert r.status is Status.VERIFIED
    assert r.issues == []


def test_doi_real_con_obra_inventada(client):
    r = verify_reference(
        "Pérez, L. y Gómez, R. (2023). Evaluación formativa con IA en el aula. Revista "
        "Imaginaria, 12(3), 45-67. https://doi.org/10.1038/nature14539",
        client,
    )
    assert r.status is Status.MISMATCH
    assert r.work.title == "Deep learning"


def test_doi_inexistente(client):
    r = verify_reference("Ruiz, A. (2022). Obra fantasma. Revista. https://doi.org/10.9999/nada", client)
    assert r.status is Status.DOI_NOT_FOUND


def test_doi_mal_copiado_sugiere_el_correcto(client):
    r = verify_reference(
        "Floridi, L. y Chiriatti, M. (2020). GPT-3: Its nature, scope, limits, and "
        "consequences. Minds and Machines, 30(4), 681-694. https://doi.org/10.1007/s11023-020-0000",
        client,
    )
    assert r.status is Status.DOI_NOT_FOUND
    assert r.suggested_doi == "10.1007/s11023-020-09548-1"


def test_sin_doi_encontrada(client):
    r = verify_reference(
        "Floridi, L. y Chiriatti, M. (2020). GPT-3: Its nature, scope, limits, and "
        "consequences. Minds and Machines, 30(4), 681-694.",
        client,
    )
    assert r.status is Status.FOUND
    assert r.suggested_doi == "10.1007/s11023-020-09548-1"


def test_sin_doi_no_encontrada(client):
    r = verify_reference("Ruiz, A. (2005). Una obra que no existe en ninguna parte. Revista, 2(1), 3-10.", client)
    assert r.status is Status.NOT_FOUND


def test_obra_ausente_con_candidatos_enganosos(client):
    # Crossref devuelve un artículo titulado igual que la revista de la referencia
    # y otro de título casi idéntico, pero de otro autor y otro año.
    r = verify_reference(
        "Siemens, G. (2005). Connectivism: A learning theory for the digital age. International "
        "Journal of Instructional Technology and Distance Learning, 2(1), 3-10.",
        client,
    )
    assert r.status is Status.NOT_FOUND


def test_titulo_con_subtitulo_separado(client):
    r = verify_reference(
        "Floridi, L. y Chiriatti, M. (2020). GPT-3: Its nature, scope, limits, and consequences "
        "revisited. Minds and Machines.",
        client,
    )
    assert r.status in (Status.FOUND, Status.REVIEW)


def test_doi_de_otra_agencia(client):
    r = verify_reference(
        "Vaswani, A. (2017). Attention is all you need. arXiv. https://doi.org/10.48550/arXiv.1706.03762",
        client,
    )
    assert r.status is Status.OTHER_AGENCY


def test_anio_y_autor_distintos(client):
    r = verify_reference(
        "Hinton, G. (2019). Deep learning. Nature. https://doi.org/10.1038/nature14539", client
    )
    assert r.status is Status.VERIFIED  # Hinton figura entre los autores
    assert [i.code for i in r.issues] == ["year_mismatch"]
    r = verify_reference(
        "Ng, A. (2016). Deep learning. Nature. https://doi.org/10.1038/nature14539", client
    )
    assert r.status is Status.REVIEW
    assert {i.code for i in r.issues} == {"author_mismatch", "year_close"}


def test_error_de_red():
    def broken(url):
        raise CrossrefError("sin conexión")

    r = verify_reference("A, B. (2020). Título. Revista.", CrossrefClient(fetch=broken))
    assert r.status is Status.ERROR


def test_modo_sin_conexion():
    results = verify_text("A, B. (2020). Uno. doi:10.1000/x\n\nC, D. (2021). Dos. R.", offline=True)
    assert [r.status for r in results] == [Status.FORMAT_ONLY] * 2
    assert results[0].issues[0].code == "doi_format"


def test_cli_json_texto_y_estricto(client, tmp_path, capsys):
    path = tmp_path / "refs.txt"
    path.write_text(
        "LeCun, Y., Bengio, Y. y Hinton, G. (2015). Deep learning. Nature. "
        "https://doi.org/10.1038/nature14539\n\n"
        "Ruiz, A. (2022). Obra fantasma. Revista. https://doi.org/10.9999/nada\n",
        encoding="utf-8",
    )
    assert main([str(path), "--format", "json"], client=client) == 0
    data = json.loads(capsys.readouterr().out)
    assert [d["status"] for d in data] == ["verified", "doi_not_found"]

    assert main([str(path), "--strict", "--lang", "en"], client=client) == 1
    out = capsys.readouterr().out
    assert "VERIFIED" in out and "DOI DOES NOT EXIST" in out

    assert main([str(path), "-f", "markdown"], client=client) == 0
    assert "# Informe de verificación" in capsys.readouterr().out


def test_titulo_parecido_con_mismo_autor_no_se_descarta(client):
    r = verify_reference("Goldie, J. (2016). Connectivism: A learning theory for the digital age. Medical Teacher.", client)
    assert r.status in (Status.FOUND, Status.REVIEW)
    assert r.work.doi == "10.3109/0142159x.2016.1173661"
