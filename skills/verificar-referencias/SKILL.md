---
name: verificar-referencias
description: Verifica si las referencias bibliográficas de un trabajo existen de verdad, contrastándolas con Crossref, y revisa su formato APA 7. Usar cuando se pida comprobar una bibliografía, detectar referencias inventadas por una IA, buscar un DOI que falta o corregir citas de un trabajo, un TFG, un TFM, una tesis o una entrada de foro. Use when asked to check, verify or fact-check a reference list, find fabricated citations or missing DOIs.
argument-hint: "[archivo con las referencias]"
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/verificar.py *)
---

# Verificar referencias APA 7

Esta skill comprueba una lista de referencias contra Crossref con la herramienta `verificapa`, incluida en el plugin. No hay que instalar nada: solo hace falta `python3` (3.10 o posterior) y conexión a `api.crossref.org` y `doi.org`.

## Pasos

1. **Reúne las referencias en un archivo de texto**, una por párrafo. Si vienen dentro de un documento (Word, PDF, mensaje de foro), extrae solo la lista de referencias. Copia el texto tal cual, sin corregir nada: los errores también son información.

2. **Ejecuta la verificación** y pide la salida en JSON:

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/verificar.py referencias.txt --format json
   ```

   Opciones útiles: `--lang en` para mensajes en inglés, `--conjunction y` o `--conjunction "&"` para exigir una forma ante el último autor, `--offline` para revisar solo el formato y `--mailto correo` para identificarse ante Crossref.

   Si en la sesión están las herramientas MCP `verificar_referencias`, `consultar_doi` y `buscar_obra`, puedes usarlas en lugar de la orden.

3. **Interpreta cada estado** con esta tabla:

   | Estado | Qué significa | Qué hacer |
   |---|---|---|
   | `verified` | El DOI existe y título, autor y año coinciden. | Darla por buena. |
   | `found` | No traía DOI, pero la obra existe. | Proponer el DOI de `suggested_doi`. |
   | `review` | Coincidencia parcial. | Comparar la referencia con el registro de Crossref y explicar la diferencia. |
   | `mismatch` | El DOI existe, pero es de otra obra. | Señalarla como muy probablemente inventada o mal copiada. Mostrar a qué obra pertenece el DOI. |
   | `doi_not_found` | El DOI no está registrado. | Señalarla. Si hay `suggested_doi`, proponer la corrección. |
   | `not_found` | Crossref no tiene nada parecido. | No concluir todavía. Ver la sección siguiente. |
   | `other_agency` | DOI válido de otra agencia (arXiv, Zenodo). | Indicar que existe, pero que no se han podido comparar los datos. |
   | `error` | Falló la conexión. | Decirlo y no dar ningún veredicto sobre esa referencia. |

4. **Redacta el informe.** Empieza por el resumen: cuántas referencias hay y cuántas tienen problemas. Después explica una a una solo las problemáticas. Deja para el final los avisos de formato (`issues` de tipo `format`).

## Cautelas obligatorias

- **«No encontrada» no significa «inventada».** Crossref cubre sobre todo artículos con DOI. Muchos libros, capítulos, informes, tesis y revistas en español no están. Antes de sospechar de una referencia `not_found`, búscala por otra vía si es posible (búsqueda web, Dialnet, Google Scholar, catálogo de la editorial). Si no puedes comprobarla, dilo así: «no he podido verificarla».
- **No acuses a nadie.** Una referencia falsa puede ser un error de copia o venir de una fuente secundaria. Describe el hecho («este DOI pertenece a otro artículo») y no la intención.
- **No inventes correcciones.** Propón un DOI o un dato corregido solo si procede del resultado de la herramienta o de una fuente que hayas consultado.
- **Las reglas de formato son pocas.** Que la herramienta no avise no garantiza que la referencia cumpla APA 7 en todo.

## Si el informe es para un estudiante

Escribe en tono constructivo y orientado a la mejora. Explica qué debe comprobar y cómo hacerlo la próxima vez: buscar el DOI en https://doi.org y contrastar el título antes de citar.
