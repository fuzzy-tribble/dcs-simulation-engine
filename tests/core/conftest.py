"""Conftest fixtures for core tests."""

from pathlib import Path
from types import SimpleNamespace
from typing import Callable

import pytest

from dcs_simulation_engine.core.run_manager import RunManager
from dcs_simulation_engine.helpers import database_helpers as dbh
from tests.helpers import patch_yml


@pytest.fixture
def game_config_minimal(
    write_yaml: Callable[[Path, str], Path], tmp_path_factory: pytest.TempPathFactory
) -> SimpleNamespace:
    """Fixture for a minimal base GameConfig."""
    base = tmp_path_factory.mktemp("cfg_minimal")
    game_config_yml = """
    name: Minimal Test Game Config
    description: A minimal game config for testing.
    characters:
      pc:
        valid:
          characters: {}
      npc:
        valid:
          characters: {}
    graph_config:
      name: Minimal test graph
      description: A minimal graph for testing with start and end nodes only.
      nodes:
        - name: echoNode
          provider: openrouter
          model: openai/gpt-oss-20b:free
          additional_kwargs: {}
          system_prompt_template: "Echo back any input message."
          state_permissions:
            read: []
            write: []
      edges:
        - from: __start__
          to: echoNode
        - from: echoNode
          to: __end__
    """
    game_config_path = base / "game_config_minimal.yml"
    write_yaml(game_config_path, game_config_yml)
    return SimpleNamespace(path=game_config_path)


@pytest.fixture
def game_config_with_branching_graph(
    game_config_minimal: SimpleNamespace,
) -> SimpleNamespace:
    """Fixture for a game config with a branching graph."""
    patch = """
    characters:
      pc:
        valid:
          characters: { hid: 'human-normative' }
      npc:
        valid:
          characters: { hid: 'flatworm' }
    graph_config:
      name: simple-test-graph
      description: |
        A two node graph for testing that branches on state and returns 
        only fixed string replies.
      nodes:
        - name: scene_setup_agent
          provider: openrouter
          model: openai/gpt-oss-20b:free
          additional_kwargs: {}
          system_prompt_template: "Reply with 'SETUP_SCENE' ONLY."
          state_permissions:
            read: []
            write: ["agent_artifacts"]
        - name: scene_continuation_agent
          provider: openrouter
          model: openai/gpt-oss-20b:free
          additional_kwargs: {}
          system_prompt_template: "Reply with 'CONTINUE_SCENE' ONLY."
          state_permissions:
            read: ["messages"]
            write: ["messages"]
      edges:
        - from: __start__
          to:
            conditional:
              - if: "len(messages) == 0"
                then: scene_setup_agent
              - else: scene_continuation_agent
        - from: scene_setup_agent
          to: __end__
        - from: scene_continuation_agent
          to: __end__
    """
    patched_yml = patch_yml(game_config_minimal.path, patch)
    return SimpleNamespace(path=patched_yml.path)


@pytest.fixture
def run(game_config_with_branching_graph: SimpleNamespace) -> RunManager:
    """Fresh RunManager instance built from the reusable YAML files.

    Kept function-scoped so each test gets a clean instance.
    """
    rm = RunManager.create(
        game_config_fpath=Path(game_config_with_branching_graph.path),
        pc_choice="human-normative",
        # npc_choice="flatworm"
    )
    return rm


@pytest.fixture
def game_config_with_player_persistence(
    game_config_minimal: SimpleNamespace,
) -> SimpleNamespace:
    """Fixture for a game config with player persistence."""
    patch = """
    enable-player-persistence: True
    characters:
      pc:
        valid:
          characters: { hid: 'human-normative' }
      npc:
        valid:
          characters: { hid: 'flatworm' }
    """
    patched_yml = patch_yml(game_config_minimal.path, patch)
    return SimpleNamespace(path=patched_yml.path)


@pytest.fixture
def persistant_run(game_config_with_player_persistence: SimpleNamespace) -> RunManager:
    """Fresh RunManager instance with player persistence enabled."""
    # create player in db and get access key
    player_data = {
        "name": "Persistant Test Player",
        "email": "persistant_test_player@example.com",
    }
    player_id, access_key = dbh.create_player(
        player_data=player_data, issue_access_key=True
    )
    rm = RunManager.create(
        game_config_fpath=Path(game_config_with_player_persistence.path),
        access_key=access_key,
    )
    return rm
