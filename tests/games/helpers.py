"""Helper functions for game config tests."""

from pathlib import Path


def discover_yaml_files() -> list[Path]:
    """Return all YAML/YML files under ./games as sorted Paths."""
    root = Path("games")
    patterns = ("*.yaml", "*.yml")
    files = {p for pat in patterns for p in root.rglob(pat)}
    return sorted(files)
