"""Allow legacy scripts to run directly from an uninstalled checkout."""

from pathlib import Path
from sys import path


def bootstrap() -> None:
    root = str(Path(__file__).resolve().parent.parent)
    if root not in path:
        path.insert(0, root)
