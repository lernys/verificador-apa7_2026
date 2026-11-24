"""El plugin de Claude: manifiestos coherentes y lanzador que funciona sin instalar."""

import json
import subprocess
import sys
from pathlib import Path

import verificapa

ROOT = Path(__file__).resolve().parents[1]


def test_manifiestos_validos_y_version_coherente():
    plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    assert plugin["version"] == verificapa.__version__
    assert f'version = "{verificapa.__version__}"' in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert market["plugins"][0]["name"] == plugin["name"] == "verificapa"
    assert market["plugins"][0]["source"] == "."
    assert market["owner"]["name"]


def test_la_skill_tiene_descripcion_y_apunta_al_lanzador():
    skill = (ROOT / "skills/verificar-referencias/SKILL.md").read_text(encoding="utf-8")
    assert skill.startswith("---\nname: verificar-referencias\ndescription: ")
    assert "${CLAUDE_SKILL_DIR}/scripts/verificar.py" in skill


def test_lanzador_funciona_sin_instalar(tmp_path):
    refs = tmp_path / "refs.txt"
    refs.write_text("A, B. (2020). Título. Revista. doi:10.1000/x\n", encoding="utf-8")
    script = ROOT / "skills/verificar-referencias/scripts/verificar.py"
    out = subprocess.run(
        [sys.executable, "-S", str(script), str(refs), "--offline", "--format", "json"],
        capture_output=True, text=True, cwd=tmp_path, env={"PATH": "/usr/bin:/bin"},
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data[0]["status"] == "format_only"
    assert data[0]["issues"][0]["code"] == "doi_format"
