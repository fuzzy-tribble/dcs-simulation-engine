"""Helpers for games."""

from pathlib import Path

import yaml
from loguru import logger


def get_game_config(game_name: str) -> str:
    """Return path to the yaml file whose top-level `name` matches `game_name`."""
    games_dir = Path(__file__).parent.parent.parent / "games"

    names_found = []
    for path in games_dir.glob("*.y*ml"):
        try:
            with path.open("r", encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            doc_name: str = doc.get("name")
            if doc_name:
                names_found.append(doc_name)
            if doc_name and doc_name.strip().lower() == game_name.strip().lower():
                return str(path)
        except Exception:
            logger.warning(
                f"Failed to load game config from {path}. Maybe syntax error? Skipping."
            )
            continue
    raise FileNotFoundError(
        f"No game config with name={game_name!r} found in {games_dir}. Found: {names_found}"
    )
