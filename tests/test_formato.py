from verificapa import check_format, parse_reference


def codes(raw, **kw):
    return [code for code, _ in check_format(parse_reference(raw), **kw)]


def test_referencia_correcta_sin_avisos():
    assert codes("A, B. y C, D. (2020). Título. Revista, 1(2), 3-4. https://doi.org/10.1000/x") == []


def test_doi_sin_formato_de_enlace():
    assert "doi_format" in codes("A, B. (2020). Título. Revista. doi:10.1000/x")
    assert "doi_format" in codes("A, B. (2020). Título. Revista. http://dx.doi.org/10.1000/x")


def test_punto_tras_enlace():
    assert "period_after_link" in codes("A, B. (2020). Título. https://doi.org/10.1000/x.")


def test_recuperado_de():
    assert "retrieved_from" in codes("A, B. (2020). Título. Recuperado de https://ejemplo.org/a")


def test_et_al_y_sin_anio():
    assert "et_al" in codes("A, B. et al. (2020). Título. Revista.")
    assert "no_year" in codes("A, B. Título sin fecha. Revista.")


def test_conjuncion_opcional():
    raw = "A, B., & C, D. (2020). Título. Revista."
    assert "conjunction" not in codes(raw)
    assert "conjunction" in codes(raw, conjunction="y")
    assert "conjunction" in codes("A, B. y C, D. (2020). Título. Revista.", conjunction="&")
