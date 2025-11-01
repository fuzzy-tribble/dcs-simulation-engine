"""App state definition for the Gradio UI."""

from queue import Queue
from threading import Thread
from typing import TypedDict

from dcs_simulation_engine.core.run_manager import SimulationManager


class AppState(TypedDict, total=False):
    """State stored in gr.State for a single browser session."""

    mode: str  # "demo" or "benchmark"
    access_token: str | None
    sim: SimulationManager
    queue: Queue[str]
    last_seen: int
    _play_thread: Thread
