"""Helper functions for widget."""

import time
from typing import Any, Dict, Iterator, Optional

import gradio as gr
from loguru import logger

from dcs_simulation_engine.core.run_manager import RunManager
from dcs_simulation_engine.widget.session_state import SessionState

FRIENDLY_GR_ERROR = (
    "Yikes! We encountered an error while processing your input."
    " Its been logged and we're looking into it. Sorry about that."
)


def spacer(h: int = 24) -> None:
    """Create a vertical spacer of given height."""
    gr.HTML(f"<div style='height:{h}px'></div>")


def wpm_to_cps(wpm: int) -> float:
    """Convert words-per-minute to characters-per-second.

    Assumes average word length of 5 characters.
    """
    return max(1.0, (wpm * 5) / 60.0)


def slow_yield_chars(
    message: str,
    wpm: int = 180,  # ~15 cps
    min_yield_interval: float = 0.03,  # don’t spam UI; yield at most ~33 FPS
) -> Iterator[str]:
    """Yield a message one character at a time, simulating human typing speed."""
    cps = wpm_to_cps(wpm)
    per_char = 1.0 / cps

    # Natural micro-pauses after punctuation
    pauses = {
        ".": 0.35,
        "!": 0.35,
        "?": 0.35,
        ",": 0.12,
        ";": 0.15,
        ":": 0.15,
        "\n": 0.22,
        "—": 0.10,
        "…": 0.20,
    }

    built = []
    next_yield_at = time.perf_counter()  # throttle UI updates

    for ch in message:
        built.append(ch)
        time.sleep(per_char)

        # add extra pause after certain punctuation
        if ch in pauses:
            time.sleep(pauses[ch])

        now = time.perf_counter()
        if now >= next_yield_at:
            yield "".join(built)
            next_yield_at = now + min_yield_interval

    # final flush
    yield "".join(built)


def stream_msg(message: str) -> Iterator[str]:
    """Streams a message at about reading speed."""
    for partial in slow_yield_chars(
        message,
        # wpm=random.randint(150, 220),
    ):
        yield partial


def create_run(state: SessionState, token_value: Optional[str] = None) -> RunManager:
    """Create a new RunManager and return it."""
    if "game_config" not in state:
        raise ValueError("App state is missing game_config required to create run.")
    if "player_id" not in state:
        state["player_id"] = None
    pc_choice = state.get("pc_choice", None)
    npc_choice = state.get("npc_choice", None)
    try:
        run = RunManager.create(
            game=state["game_config"].name,
            source="widget",
            pc_choice=pc_choice,
            npc_choice=npc_choice,
            player_id=state["player_id"],
        )
    except Exception as e:
        logger.error(f"Error creating RunManager in _create_run: {e}", exc_info=True)
        raise gr.Error(FRIENDLY_GR_ERROR)
    return run


def format(msg_dict: Dict[str, Any]) -> str:
    """Format dict style message into a markdown formatted string for gradio display."""
    if not isinstance(msg_dict, dict):
        logger.error(
            f"Received non-dict message in _format: {msg_dict}. Returning str()."
        )
        raise gr.Error(FRIENDLY_GR_ERROR)
    if "type" not in msg_dict or "content" not in msg_dict:
        logger.warning(
            f"Received malformed message in _format: {msg_dict}."
            " Dict must include 'type' and 'content' keys."
        )
        raise gr.Error(FRIENDLY_GR_ERROR)
    t = (msg_dict.get("type") or "info").lower()
    c = msg_dict.get("content") or ""
    if not c:
        logger.warning("Received empty content in _format.")
    if t == "warning":
        return f"⚠️ {c}"
    elif t == "error":
        return f"❌ {c}"
    elif t == "info":
        return c
    elif t == "system" or t == "assistant" or t == "ai":
        return c
    else:
        logger.warning(f"Unknown message type '{t}' in _format; returning raw content.")
        return c
