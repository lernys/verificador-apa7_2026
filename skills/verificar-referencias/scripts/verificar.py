#!/usr/bin/env python3
"""Lanza verificapa desde el plugin, sin instalar nada."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from verificapa.cli import main  # noqa: E402

raise SystemExit(main())
