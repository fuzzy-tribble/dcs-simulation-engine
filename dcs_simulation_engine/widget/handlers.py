"""Web handlers for Gradio interface to the DCS Simulation Engine.

Send → enqueue → sim.play consumes → timer polls state → new messages appear.

"""

from __future__ import annotations

from queue import Queue
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple

import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger

from dcs_simulation_engine.core.run_manager import RunManager
from dcs_simulation_engine.widget.state import AppState
from dcs_simulation_engine.widget.ui.landing import LandingUI
from dcs_simulation_engine.widget.ui.consent import ConsentUI

Message = Dict[str, str]


# def _make_input_provider(state: AppState) -> Callable[[], str]:
#     """Create a blocking input provider that feeds user messages from a Queue.

#     The returned callable mirrors your CLI `input_provider`: it blocks until a
#     user message is available, then returns that message to `RunManager.play()`.

#     Args:
#         state: App state containing the active simulation and the message queue.

#     Returns:
#         Callable that takes no arguments and returns the next user message.

#     Raises:
#         ValueError: If the simulation state was not initialized properly.
#     """
#     q: Queue[str] = state["queue"]
#     sim: RunManager = state["sim"]

#     def input_provider() -> str:
#         """A blocking input provider for the simulation's play loop.

#         It just reads from the queue.
#         """
#         if sim.state is None:
#             raise ValueError("Simulation state was not initialized properly.")
#         msgs = sim.state.get("messages", [])
#         logger.debug(f"input_provider sees {len(msgs)} messages: {msgs}")
#         return q.get()

#     return input_provider


# def _ensure_play_running(state: AppState) -> None:
#     """Start the simulation's play loop in a background daemon thread if needed.

#     Spawns a single thread that calls `sim.play(input_provider=...)`. The play loop
#     will block on the input provider until `on_send` pushes messages into the queue.

#     Args:
#         state: App state. Must contain "sim" and "queue". On success, adds
#             "_play_thread" to the state if it didn't exist or had stopped.
#     """
#     existing: Optional[Thread] = state.get("_play_thread")
#     if existing and existing.is_alive():
#         return

#     sim: RunManager = state["sim"]
#     ip = _make_input_provider(state)

#     thread = Thread(target=lambda: sim.play(input_provider=ip), daemon=True)
#     thread.start()
#     state["_play_thread"] = thread


# ---------- Gradio Handlers ----------
def on_play(state: AppState, token_value: str) -> Tuple[AppState, dict[str, Any]]:
    """Handle clicking the Play button on the landing page.

    - tries calling RunManager.create and updates state with run or permission error
    """
    logger.debug(f"on_play called with token: {token_value}")
    if state["access_gated"] and not token_value:
        return state, gr.update(visible=True, value="Access token required")
    
    try:
        run = RunManager.create(
            game=state["game_name"],
            source="widget",
            access_key=token_value
            )
        state["run"] = run
        token_error_box_update = {}
        token_box_update = gr.update(value="")
        return state, token_box_update, token_error_box_update
    except PermissionError as e:
        logger.warning(f"PermissionError in on_play: {e}")
        state["permission_error"] = str(e)
        token_error_box_update = gr.update(visible=True)
        token_box_update = gr.update(value="")
        return state, token_box_update, token_error_box_update
    except Exception as e:
        logger.error(f"Error while handling on_play: {e}", exc_info=True)
        raise
    

def on_generate_token(state: AppState):
    """Handle clicking the Generate New Access Token button on the landing page.

    Takes landing container and consent container and sets visibility to show consent form and not landing.
    """
    logger.debug("on_generate_token called")
    updated_landing = gr.update(visible=False)
    updated_consent = gr.update(visible=True)
    return state, updated_landing, updated_consent

def on_consent_back(state: AppState):
    """Handle clicking the Back button on the consent page.

    Takes landing container and consent container and sets visibility to show landing and not consent form.
    """
    logger.debug("on_consent_back called")
    updated_landing = gr.update(visible=True)
    updated_consent = gr.update(visible=False)
    return state, updated_landing, updated_consent

def on_consent_submit(state: AppState, field_names: List[str], *field_values: List[Any]):
    """Handle clicking the I Agree & Continue button on the consent page.

    - creates player with consent data, issues access token
    - takes landing container and consent container and sets visibility to show landing and not consent form.
    """
    # TODO: validate consent fields and if not valid return error message text below
    consent_data = dict(zip(field_names, field_values))
    logger.debug(f"on_consent_submit called with field_values: {consent_data}")
    # create player with consent data, issue access token
    from dcs_simulation_engine.helpers import database_helpers as dbh
    try:
        player_id, access_key = dbh.create_player(
            player_data=consent_data,
            issue_access_key=True
        )
        logger.debug(f"Created player {player_id} with access key.")
        updated_form_group = gr.update(visible=False)
        updated_token_group = gr.update(visible=True)
        updated_token_text = gr.update(placeholder=access_key)
        return state, updated_form_group, updated_token_group, updated_token_text
    except Exception as e:
        logger.error(f"Error creating player in on_consent_submit: {e}", exc_info=True)
        raise


def on_token_continue(state: AppState):
    """Handle clicking the Continue button on the token display page.

    Takes landing container and consent container and sets visibility to show landing and not consent form.
    """
    logger.debug("on_token_continue called")
    updated_landing = gr.update(visible=True)
    updated_token_group = gr.update(visible=False)
    # IMPORTANT: clear token display
    updated_token_text = gr.update(placeholder="")  # clear placeholder
    logger.debug("Cleared token display on continue.")
    updated_consent = gr.update(visible=False)
    return state, updated_landing, updated_token_group, updated_consent, updated_token_text

def poll_fn(
    chat: List[Message], state: Dict[str, Any]
) -> Tuple[List[Message], Dict[str, Any]]:
    """Poll for new messages from the simulation engine to update the chat history."""
    sim: Optional[RunManager] = state.get("sim")
    if sim is None or sim.state is None or "last_seen" not in state:
        return chat, state, gr.update()
    if sim.stopped:
        # don't poll for new messages if the sim is stopped
        # TODO - display results from sim run data
        return (
            chat
            + [
                {
                    "role": "assistant",
                    "content": "The simulation has ended.",
                }
            ],
            state,
            gr.update(active=False, interactive=False),
        )
    msgs = sim.state.get("messages", [])
    # logger.debug(f"poll_fn sees {len(msgs)} messages, last_seen={state['last_seen']}")
    for m in msgs[state.get("last_seen") :]:
        logger.debug(f"poll_fn appending message: {m} to chat: {chat}")
        if isinstance(m, AIMessage):
            role = "assistant"
        elif isinstance(m, HumanMessage):
            role = "user"
        else:
            role = "assistant"  # fallback

        chat.append({"role": role, "content": m.content})

    state["last_seen"] = len(msgs)
    return chat, state, gr.update()  # keep ticking


# def on_send(
#     msg: str, chat: List[Message], state: Dict[str, Any]
# ) -> Tuple[List[Message], str]:
#     """Handle a user message: enqueue it and return the latest engine reply.

#     Behavior mirrors the CLI:
#     1) Puts the user message into the queue consumed by the input provider.
#     2) Waits for the engine to append a new message to `sim.state["messages"]`.
#     3) Appends the (user, assistant) pair to the Gradio Chatbot history.

#     Args:
#         msg: The user's input text from the textbox.
#         chat: Current Chatbot history.
#         state: gr.State dictionary containing the active simulation and queue.

#     Returns:
#         Tuple[List[Message], str]: Updated Chatbot history and an empty string
#         to clear the input textbox.

#     Notes:
#         Includes a safety timeout (120s) to avoid indefinite waiting.
#     """
#     app_state: AppState = AppState(**state) if isinstance(state, dict) else AppState()
#     sim: Optional[RunManager] = app_state.get("sim")
#     if not sim:
#         # TODO: fix - this isn't displayed anywhere...
#         return ([{"role": "assistant", "content": "Load a simulation first."}], "")

#     if sim.stopped:
#         # don't accept new messages if the sim is stopped
#         return (
#             chat
#             + [
#                 {
#                     "role": "assistant",
#                     "content": "The simulation has ended.",
#                 }
#             ],
#             "",
#         )

#     # Ensure the play loop is alive (idempotent)
#     _ensure_play_running(app_state)

#     # Enqueue user message for the input provider
#     if "queue" not in app_state:
#         raise ValueError("App state is missing the message queue.")
#     logger.debug(f"on_send enqueuing message: {msg}")
#     app_state["queue"].put(msg)

#     return chat, ""
