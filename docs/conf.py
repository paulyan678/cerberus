"""Sphinx configuration for the Cerberus documentation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

project = "Cerberus"
copyright = "2024-2026, Paul Yan, Juho Kim, Minchan Kim, and Jacky Kuang"
author = "Paul Yan, Juho Kim, Minchan Kim, and Jacky Kuang"
version = "0.1"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
language = "en"
pygments_style = "sphinx"

html_theme = "alabaster"
html_title = "Cerberus documentation"
html_theme_options = {
    "description": "CCTV event analysis and retrieval toolkit",
    "fixed_sidebar": True,
}
