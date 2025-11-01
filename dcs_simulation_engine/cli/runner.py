# cli.py
from typing import Optional

from loguru import logger
from rich.console import Console

from dcs_simulation_engine.cli.configuration import load_theme
from dcs_simulation_engine.core.run_manager import RunManager


def run_cli(
    game: str,
    source: str,
    pc_choice: Optional[str] = None,
    npc_choice: Optional[str] = None,
    access_key: Optional[str] = None,
    custom_theme_path: Optional[str] = None,
) -> None:
    """Run the CLI interaction loop."""
    console = Console()
    theme = load_theme(custom_theme_path)

    try:
        with console.status("Setting up simulation...", spinner="dots"):
            run = RunManager.create(
                game=game,
                source=source,
                pc_choice=pc_choice,
                npc_choice=npc_choice,
                access_key=access_key,
            )
    except Exception as e:
        console.print(
            f"Failed to setup simulation with error: {e}", style=theme["error"]
        )
        logger.exception(f"Failed to setup simulation with error: {e}")
        raise

    last_seen = 0

    def rich_input_provider() -> str:
        nonlocal last_seen
        if run.state is None:
            raise ValueError("Simulation state was not initialized properly.")

        sp = run.state.get("special_user_message")
        if sp:
            console.print()  # blank line
            console.print(sp["content"], style=theme["info"])
            run.state["special_user_message"] = None

        if run.state["lifecycle"] == "EXIT":
            return ""

        events = run.state["events"]
        if len(events) > last_seen and events[-1].type == "ai":
            last_msg = events[-1]
            console.print()  # blank line
            console.print(f"{last_msg.content}", style=theme["simulation-response"])
            last_seen = len(events)

        console.print()  # blank line
        # Style the prompt via print + input (keeps YAML-driven styles)
        console.print("what do you do next? ", style=theme["user-prompt"], end=" ")
        return console.input().strip()

    console.rule("Game Started", style=theme["intro"])
    # TODO: consider adding ... while simulation engine turns are running
    run.play(input_provider=rich_input_provider)
    reason = run.exit_reason
    console.rule(f"Game Exited (reason: {reason})", style=theme["outtro"])
