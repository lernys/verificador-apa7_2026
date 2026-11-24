# verificapa

**Verificador de referencias APA 7.** Comprueba si las referencias de un trabajo existen de verdad y avisa de las que parecen inventadas.

[![pruebas](https://github.com/lernys/verificador-apa7_2026/actions/workflows/pruebas.yml/badge.svg)](https://github.com/lernys/verificador-apa7_2026/actions/workflows/pruebas.yml)
[![Licencia MIT](https://img.shields.io/badge/licencia-MIT-blue.svg)](LICENSE)

🇬🇧 [English version](README.en.md)

## El problema

Los modelos de lenguaje inventan referencias. Tienen autores creíbles, revistas reales y un DOI con buen aspecto, pero la obra no existe. Cualquier docente que corrige trabajos se las encuentra, y comprobarlas una a una lleva horas.

`verificapa` hace esa comprobación por usted. Lee una lista de referencias, consulta cada una en [Crossref](https://www.crossref.org) y le dice cuáles puede dar por buenas y cuáles debe mirar.

## Qué detecta

| Estado | Qué significa |
|---|---|
| ✔ Verificada | El DOI existe y el título, el autor y el año coinciden. |
| ✔ Encontrada | La referencia no trae DOI, pero la obra existe. Se sugiere el DOI. |
| ? Revisar a mano | La coincidencia es parcial: cambia el autor o el título se parece solo en parte. |
| ✘ El DOI es de otra obra | El DOI existe, pero pertenece a otro artículo. Es la señal más clara de referencia inventada. |
| ✘ El DOI no existe | Ninguna agencia lo tiene registrado. |
| ✘ No encontrada | Crossref no tiene nada parecido. |
| ~ Fuera de Crossref | El DOI es válido, pero lo gestiona otra agencia, como DataCite (arXiv, Zenodo). |

Además revisa varios descuidos de formato de APA 7: el DOI que no está escrito como enlace, el punto final tras un DOI o una URL, el «Recuperado de» que la séptima edición eliminó, el «et al.» en la lista de referencias y la falta de año.

## Instalación

Necesita Python 3.10 o posterior. No tiene dependencias.

```bash
pip install git+https://github.com/lernys/verificador-apa7_2026
```

## Uso

Guarde las referencias en un archivo de texto, una por párrafo o una por línea:

```bash
verificapa referencias.txt
```

Con el archivo de [ejemplos/referencias.txt](ejemplos/referencias.txt) el informe es este:

```text
[1] ✔ VERIFICADA
    LeCun, Y., Bengio, Y. y Hinton, G. (2015). Deep learning. Nature, 521(7553), 436-444. https://doi.org/10.1038/nature14539
    Crossref: LeCun, Bengio, Hinton (2015). Deep learning. Nature. https://doi.org/10.1038/nature14539

[2] ✔ ENCONTRADA (FALTA EL DOI)
    Floridi, L. y Chiriatti, M. (2020). GPT-3: Its nature, scope, limits, and consequences. Minds and Machines, 30(4), 681-694.
    Crossref: Floridi, Chiriatti (2020). GPT-3: Its Nature, Scope, Limits, and Consequences. Minds and Machines. https://doi.org/10.1007/s11023-020-09548-1
    DOI sugerido: https://doi.org/10.1007/s11023-020-09548-1

[3] ✘ EL DOI ES DE OTRA OBRA
    Pérez, L. y Gómez, R. (2023). Inteligencia artificial generativa y evaluación formativa en el aula universitaria. Revista Imaginaria de Educación, 12(3), 45-67. https://doi.org/10.1038/nature14539
    → El DOI existe, pero Crossref lo asigna a esta otra obra. Es el patrón típico de una referencia inventada.
    Crossref: LeCun, Bengio, Hinton (2015). Deep learning. Nature. https://doi.org/10.1038/nature14539
```

La tercera referencia es inventada a propósito: usa un DOI real que pertenece a otro artículo.

### Opciones

| Opción | Para qué sirve |
|---|---|
| `--format text\|json\|markdown` | Formato del informe. `json` sirve para integrarlo en otras herramientas. |
| `--lang es\|en` | Idioma del informe. |
| `--mailto correo` | Su correo. Crossref atiende antes a quien se identifica. |
| `--conjunction y\|&` | Exige «y» o «&» ante el último autor. Por defecto no se comprueba. |
| `--offline` | Solo revisa el formato, sin conexión. |
| `--strict` | Termina con código 1 si hay referencias dudosas. Útil en procesos automáticos. |
| `-o archivo` | Guarda el informe en un archivo. |

También lee de la entrada estándar: `pbpaste | verificapa -` en Mac.

### Desde Python

```python
from verificapa import verify_text

for r in verify_text(open("referencias.txt", encoding="utf-8").read()):
    print(r.index, r.status.value, r.suggested_doi)
```

## Límites que conviene conocer

- **«No encontrada» no significa «inventada».** Crossref cubre sobre todo artículos con DOI. Muchos libros, informes, tesis y revistas en español no están. En esos casos la herramienta le indica dónde mirar, pero la decisión es suya.
- **El análisis es heurístico.** Las referencias mal formadas pueden leerse mal. Por eso existe el estado «Revisar a mano».
- **Las reglas de formato son pocas y prudentes.** Preferimos callar a dar un aviso falso. No sustituyen al manual de APA.
- **No acusa a nadie.** Una referencia inventada puede ser un error de copia. El informe es un punto de partida para hablar con el estudiante, no una prueba.

## Cómo contribuir

Toda ayuda es bienvenida, también la de quien no programa. Lea [CONTRIBUTING.md](CONTRIBUTING.md).

## Autoría y licencia

Creado por [Fernando Santamaría González](https://fernandosantamaria.com) dentro de [IAforTeachers](https://iaforteachers.com), comunidad sobre inteligencia artificial en educación superior para docentes hispanohablantes.

Licencia [MIT](LICENSE). Los datos proceden de la API pública de Crossref.
