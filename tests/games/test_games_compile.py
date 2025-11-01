"""Tests that all games in the games/ directory compile without errors.

This module discovers every YAML file under ./games and verifies that each one
can be compiled (i.e., a RunManager can be created) without raising exceptions.
Each file is shown as a separate pytest case via parametrization.
"""

from __future__ import annotations

from pathlib import Path
from typing import NewType

import pytest
from helpers import discover_yaml_files
from loguru import logger

from dcs_simulation_engine.core.run_manager import RunManager

#: Strong alias for paths to game config files.
GameConfigPath = NewType("GameConfigPath", Path)


YAML_FILES: list[Path] = discover_yaml_files()


@pytest.mark.unit
def test_games_directory_not_empty() -> None:
    """Ensure there is at least one YAML file under ./games."""
    logger.debug(f"Discovered game config files: {YAML_FILES!r}")
    assert YAML_FILES, "No YAML files found under ./games. Add configs to test."


@pytest.mark.compile
@pytest.mark.parametrize("cfg_path", YAML_FILES, ids=[p.name for p in YAML_FILES])
def test_all_games_compile(cfg_path: Path) -> None:
    """For each config, ensure RunManager.create(...) succeeds.

    Relies on test_game_config.py to cover parsing/validation details.
    Will failr if
    """
    try:
        logger.debug(f"Creating RunManager for: {cfg_path}")
        RunManager.create(
            game=cfg_path,
            source="pytest",
            pc_choice=None,
            npc_choice=None,
            access_key=None,
        )
        logger.debug("RunManager created successfully")
    except Exception as exc:
        pytest.fail(f"Failed to compile game from config: {cfg_path}\n{exc!r}")
