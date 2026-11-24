from verificapa import parse_reference, split_references

REF = (
    "García-Peñalvo, F. J., López, M. A. y Pérez, A. (2024). La IA generativa en la "
    "universidad: retos y límites. Revista de Educación, 12(3), 45-67. "
    "https://doi.org/10.1234/abc.2024.001"
)


def test_campos_basicos():
    ref = parse_reference(REF)
    assert ref.authors == ["García-Peñalvo", "López", "Pérez"]
    assert ref.year == "2024"
    assert ref.title == "La IA generativa en la universidad: retos y límites"
    assert ref.container == "Revista de Educación"
    assert ref.doi == "10.1234/abc.2024.001"


def test_autores_con_ampersand_y_cursiva_markdown():
    ref = parse_reference("Smith, J. A., & Jones, B. (2019). *A short title*. Publisher.")
    assert ref.authors == ["Smith", "Jones"]
    assert ref.title == "A short title"
    assert ref.doi is None


def test_autor_institucional_y_sin_fecha():
    ref = parse_reference("UNESCO. (s. f.). Guía para el uso de la IA. https://unesco.org/guia")
    assert ref.authors == ["UNESCO"]
    assert ref.year == "s. f."
    assert ref.url == "https://unesco.org/guia"


def test_doi_con_punto_final_y_parentesis():
    assert parse_reference("A, B. (2020). T. J. doi:10.1016/S0140-6736(20)30183-5.").doi == (
        "10.1016/S0140-6736(20)30183-5"
    )
    assert parse_reference("A, B. (2020). T. J. (https://doi.org/10.1000/xyz).").doi == "10.1000/xyz"


def test_titulo_con_pregunta():
    ref = parse_reference("Kasneci, E. (2023). ChatGPT for good? On opportunities. Learning, 103.")
    assert ref.title.startswith("ChatGPT for good?")


def test_sin_anio():
    ref = parse_reference("Texto que no es una referencia")
    assert ref.year is None and ref.authors == []


def test_separa_por_lineas_en_blanco_y_lineas_partidas():
    text = "Referencias\n\nA, B. (2020). Uno.\nRevista, 1.\n\n- C, D. (2021). Dos. Editorial.\n"
    assert split_references(text) == [
        "A, B. (2020). Uno. Revista, 1.",
        "C, D. (2021). Dos. Editorial.",
    ]


def test_separa_una_por_linea():
    text = "1. A, B. (2020). Uno. R.\n2. C, D. (2021). Dos. R.\n[3] E, F. (2022). Tres. R."
    assert len(split_references(text)) == 3
