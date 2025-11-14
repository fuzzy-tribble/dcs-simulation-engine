"""Helpers for games."""

from pathlib import Path

import yaml
from loguru import logger


def get_game_config(game: str) -> str:
    """Return the path to a YAML game config.

    Accepts either:
      - A game name (matched against built-in configs in games/)
      - A filesystem path to a custom YAML config
    """
    # First: treat `game` as a path
    possible_path = Path(game).expanduser()
    if possible_path.is_file() and possible_path.suffix.lower() in {".yml", ".yaml"}:
        return str(possible_path)

    # Otherwise: treat it as a built-in game name
    games_dir = Path(__file__).parent.parent.parent / "games"

    names_found = []
    for path in games_dir.glob("*.y*ml"):
        try:
            with path.open("r", encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            doc_name = doc.get("name")

            if not doc_name:
                logger.warning(
                    f"Game config {path} has no top-level 'name' field. Skipping."
                )
                continue

            names_found.append(doc_name)

            if doc_name.strip().lower() == game.strip().lower():
                return str(path)

        except Exception:
            logger.warning(
                f"Failed to load game config from {path}. Maybe syntax error? Skipping."
            )
            continue

    raise FileNotFoundError(
        f"No game config matching {game!r} found. " f"Found built-ins: {names_found}"
    )
