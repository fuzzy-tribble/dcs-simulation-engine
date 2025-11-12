"""Helper functions for widget."""

import time
from typing import Any, Dict, Iterator, Optional

import gradio as gr
from loguru import logger

from dcs_simulation_engine.core.run_manager import RunManager
from dcs_simulation_engine.widget.constants import USER_FRIENDLY_EXC
from dcs_simulation_engine.widget.session_state import SessionState


def cleanup(state: gr.State) -> None:
    """Clean up resources associated with a session."""
    logger.debug("Cleaning up session resources")
    session_state: SessionState = state.value
    if "run" not in session_state:
        logger.debug("No 'run' in session state to clean up")
        return
    try:
        logger.debug("Exiting simulation...")
        session_state["run"].exit(reason="session deleted")
    except Exception:
        logger.exception("Failed to cleanly exit simulation on delete")
    finally:
        logger.debug("Session cleanup complete.")


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


# TODO: don't know this is necessary....double yield...yucl
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
        logger.error("App state missing game_config in _create_run.")
        raise gr.Error(USER_FRIENDLY_EXC)
    if "player_id" not in state:
        state["player_id"] = None
    if "pc_choice" not in state:
        state["pc_choice"] = None
    if "npc_choice" not in state:
        state["npc_choice"] = None
    try:
        run = RunManager.create(
            game=state["game_config"].name,
            source="widget",
            pc_choice=state["pc_choice"],
            npc_choice=state["npc_choice"],
            player_id=state["player_id"],
        )
    except Exception as e:
        logger.error(f"Error creating RunManager in _create_run: {e}", exc_info=True)
        raise gr.Error(USER_FRIENDLY_EXC)
    return run


def format(msg_dict: Dict[str, Any]) -> str:
    """Format dict style message into a markdown formatted string for gradio display."""
    if not isinstance(msg_dict, dict):
        logger.error(
            f"Received non-dict message in _format: {msg_dict}. Returning str()."
        )
        raise gr.Error(USER_FRIENDLY_EXC)
    if "type" not in msg_dict or "content" not in msg_dict:
        logger.warning(
            f"Received malformed message in _format: {msg_dict}."
            " Dict must include 'type' and 'content' keys."
        )
        raise gr.Error(USER_FRIENDLY_EXC)
    t = (msg_dict.get("type") or "info").lower()
    c = msg_dict.get("content") or ""
    if not c:
        logger.warning("Received empty content in _format.")
    if t == "warning":
        return f"# ⚠️ Warning\n{c}"
    elif t == "error":
        return f"# ❌ Error\n{c}"
    elif t == "info":
        return c
    elif t == "system" or t == "assistant" or t == "ai":
        return c
    else:
        logger.warning(f"Unknown message type '{t}' in _format; returning raw content.")
        return c
