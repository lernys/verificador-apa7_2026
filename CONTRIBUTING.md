# Cómo contribuir

Gracias por su interés. Este proyecto nace en la comunidad de [IAforTeachers](https://iaforteachers.com) y agradece cualquier ayuda, también la de quien no programa.

## Sin programar

- **Avise de un fallo.** Si una referencia real aparece como no encontrada, o una inventada pasa por buena, abra una incidencia y pegue la referencia tal cual.
- **Proponga una regla de formato.** Indique la regla de APA 7, un ejemplo correcto y otro incorrecto.

## Programando

```bash
git clone https://github.com/lernys/verificador-apa7_2026
cd verificador-apa7_2026
pip install -e ".[dev]"
pytest
```

Unas pocas normas:

1. Cada cambio llega con su prueba. Las pruebas no usan la red: Crossref se simula en `tests/conftest.py`.
2. El paquete no tiene dependencias externas y debe seguir así.
3. Las reglas de formato han de ser prudentes. Es preferible callar a dar un aviso falso.
4. Todo mensaje al usuario se escribe en español y en inglés, en `src/verificapa/messages.py`.

## Ideas abiertas

- Analizar capítulos de libro, tesis e informes con más detalle.
- Consultar otras fuentes cuando Crossref no responde: OpenAlex, DataCite, Dialnet.
- Leer referencias desde archivos `.docx` y BibTeX.
- Añadir más reglas de formato de APA 7.
