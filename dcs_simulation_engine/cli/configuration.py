"""CLI configuration management."""

from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

DEFAULT_THEME = {
    "intro": "bold blue",
    "outtro": "bold blue",
    "info": "bold bright_black",
    "user-prompt": "bold cyan",
    "simulation-response": "bold green",
    "error": "bold red",
}


def load_theme(config_path: Optional[str] = None) -> dict:
    """Load the CLI theme from a config file."""
    try:
        if config_path is None:
            return DEFAULT_THEME.copy()
        p = Path(config_path)
        if not p.exists():
            logger.warning(f"Theme file not found at {p}; using defaults.")
            return DEFAULT_THEME.copy()
        with p.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
            theme = config.get("theme") or {}  # your YAML shape
            return {**DEFAULT_THEME, **theme}  # fill any gaps
    except Exception as e:
        logger.warning(f"Failed to load theme from {config_path}: {e}")
        return DEFAULT_THEME.copy()
