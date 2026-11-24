# verificapa

**APA 7 reference verifier.** Checks whether the references in a paper really exist and flags the ones that look fabricated.

🇪🇸 [Versión en español](README.md)

## The problem

Language models make up references. They come with plausible authors, real journals and a good-looking DOI, but the work does not exist. Every teacher who grades papers runs into them, and checking them one by one takes hours.

`verificapa` does that check for you. It reads a reference list, looks each entry up in [Crossref](https://www.crossref.org) and tells you which ones hold and which ones need a closer look.

## What it detects

| Status | Meaning |
|---|---|
| ✔ Verified | The DOI exists and title, author and year match. |
| ✔ Found | The reference has no DOI, but the work exists. A DOI is suggested. |
| ? Review by hand | Partial match: the author differs or the title is only similar. |
| ✘ DOI belongs to another work | The DOI exists but points to a different article. The clearest sign of a fabricated reference. |
| ✘ DOI does not exist | No agency has it on record. |
| ✘ Not found | Crossref has nothing similar. |
| ~ Outside Crossref | The DOI is valid but managed by another agency, such as DataCite (arXiv, Zenodo). |

It also checks a few common APA 7 format slips: a DOI not written as a link, a period after a DOI or URL, the "Retrieved from" that the 7th edition dropped, "et al." in the reference list, and a missing year.

## Install

Python 3.10 or later. No dependencies, except for the optional MCP server.

```bash
pip install git+https://github.com/lernys/verificador-apa7_2026
```

## Usage

Save the references in a text file, one per paragraph or one per line:

```bash
verificapa references.txt --lang en
```

Options: `--format text|json|markdown`, `--lang es|en`, `--mailto you@example.org` (Crossref polite pool), `--conjunction y|&`, `--offline` (format checks only), `--strict` (exit code 1 when doubtful references are found), `-o file`.

From Python:

```python
from verificapa import verify_text

for r in verify_text(open("references.txt", encoding="utf-8").read()):
    print(r.index, r.status.value, r.suggested_doi)
```

## Claude Code plugin

The easiest way to use it. The plugin gives Claude a skill that verifies reference lists and reads the results with due caution. Nothing else to install: it only needs `python3`.

```text
/plugin marketplace add lernys/verificador-apa7_2026
/plugin install verificapa@iaforteachers
```

Then just ask: "verify the references in this paper". The skill instructions are written in Spanish; Claude answers in your language.

## Use it inside Claude (MCP server)

`verificapa` ships an [MCP](https://modelcontextprotocol.io) server, so Claude and other compatible assistants can verify references during a conversation. Three read-only tools: `verificar_referencias` (verify a whole list), `consultar_doi` (does this DOI exist, and whose is it?) and `buscar_obra` (find the works closest to a reference or title).

```bash
pip install "verificapa[mcp] @ git+https://github.com/lernys/verificador-apa7_2026"
claude mcp add verificapa -- verificapa-mcp
```

For Claude Desktop, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "verificapa": {
      "command": "verificapa-mcp",
      "env": { "VERIFICAPA_MAILTO": "you@example.org" }
    }
  }
}
```

`VERIFICAPA_MAILTO` is optional; it identifies your requests to Crossref.

## Limits worth knowing

- **"Not found" does not mean "fabricated".** Crossref mostly covers articles with a DOI. Many books, reports, theses and Spanish-language journals are missing.
- **Parsing is heuristic.** Malformed references may be misread, hence the "Review by hand" status.
- **Format rules are few and conservative.** They do not replace the APA manual.
- **It accuses no one.** The report is a starting point for a conversation with the student, not evidence.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) (in Spanish; issues and pull requests in English are welcome).

## Author and licence

Created by [Fernando Santamaría González](https://fernandosantamaria.com) at [IAforTeachers](https://iaforteachers.com). [MIT](LICENSE) licence. Data from the public Crossref API.
