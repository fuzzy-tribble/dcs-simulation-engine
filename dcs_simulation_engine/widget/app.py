"""Gradio app construction for the simulation engine.

Adds a centered title and an Instructions panel derived from the loaded
simulation's characters (A/B) and graph, similar to the CLI UI.
"""

from __future__ import annotations

import time
from typing import Tuple

import gradio as gr
from gradio.themes import Soft

from dcs_simulation_engine.widget.handlers import on_load, on_send, poll_fn
from dcs_simulation_engine.widget.state import AppState

from dcs_simulation_engine.core.game_config import GameConfig
from dcs_simulation_engine.helpers.game_helpers import get_game_config
from loguru import logger
# TODO: gradio has a built-in API (see "Use via API" as bottom of rendered page). Condier using gradio apo for demo instead of hosting ourselves.

def build_app(game_name: str = "explore") -> gr.Blocks:
    """Build the Gradio UI for running simulations."""
    logger.info(f"Building Gradio app for game '{game_name}'")

    # try loading game config based on provided game
    try:
        game_config_path = get_game_config(game_name)
        game_config = GameConfig.from_yaml(game_config_path)
    except Exception as e:
        gr.Error(f"Failed to load game config: {e}")
        raise e
    
    # try to determine access mode from game config
    try: 
        access_gate_required = not bool(game_config.is_player_allowed(player_id=None))
        logger.debug(f"Access gate required: {access_gate_required}")
    except Exception as e:
        gr.Error(f"Failed to determine access mode from game config: {e}")
        raise e

    with gr.Blocks(title="DCS Simulation Engine", theme=Soft()) as app:
        # WIP banner
        gr.HTML('<div style="text-align:center" id="banner">🚧 <b>W.I.P.</b> This app is a work in progress. 🚧</div>')

        # light/dark theme toggle
        gr.HTML(
            """    
                        <style>
                        #theme-toggle {
                            position: absolute;
                            top: 10px;
                            right: 10px;
                            z-index: 999;
                            background: #444;
                            color: white;
                            border-radius: 50%;
                            width: 40px;
                            height: 40px;
                            text-align: center;
                            line-height: 40px;
                            cursor: pointer;
                            font-size: 18px;
                            border: none;
                        }
                        #theme-toggle:hover {
                            background: #666;
                        }
                        </style>
                        """
        )

        toggle = gr.Button("🌗", elem_id="theme-toggle")
        toggle.click(
            fn=None,
            js="""     
                        () => {
                        const url = new URL(window.location);
                        const cur = url.searchParams.get('__theme') || 'system';
                        const next = cur === 'dark' ? 'light' : 'dark';
                        url.searchParams.set('__theme', next);
                        window.location.replace(url);
                        }
                        """,
        )

        # title
        gr.Markdown(
            f"""
            <div style='text-align:center'>
            <h1 style='margin-bottom:0'>{game_config.name.title()}</h1>
            <p style='margin-top:6px;color:#666'>A DCS Simulation Engine Game</p>
            </div>
            """
        )
        mode_md = gr.Markdown("", elem_id="run-mode", visible=False)

        state = gr.State(AppState())
        state.value["game_name"] = game_config.name
        state.value["game_description"] = game_config.description

        # Consent form
        consent_form = gr.Group(visible=False)
        with consent_form:
            # 

        # Ungated landing page (lets players in without access token)
        ungated_landing = gr.Group(visible=not access_gate_required)
        with ungated_landing:
            # top spacing
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
            # bottom spacing
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
            # play button
            with gr.Row():
                with gr.Column(scale=1):
                    pass
                with gr.Column(scale=0, min_width=220):
                    play_btn = gr.Button("Play", variant="primary")
                with gr.Column(scale=1):
                    pass
                # spacing row
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
            ungated_msg = gr.Markdown("", visible=False)

        # Gates landing page (requires access token)
        gated_landing = gr.Group(visible=access_gate_required)
        with gated_landing:
            # TODO: add spacing (top and sides)
            gr.Markdown(
                """
## Welcome

Thank you for your interest in participating in our research. We are exploring how different types of cognitive systems interact with each other through gameplay.

You've been given this access link to play a game as part of your participation in our study.

### Instructions

To continue, please enter your access token below.

- If you don't have an access token, or you've lost it, you'll need to complete the participant consent form again.
- For privacy and security reasons, we do not store access tokens and cannot recover them for you.
- Please keep your token somewhere safe.

*If you need help, have questions, or encounter any issues, please email McKinnley Workman at mworkman9@gatech.edu*
        """.strip()  # noqa: E501
            )
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing

            # Benchmark row: token + begin button
            with gr.Row():
                with gr.Column(scale=1):
                    pass
                with gr.Column(scale=3):
                    token_box = gr.Textbox(
                        label="", # don't show label
                        placeholder="ak-xxxx-xxxx-xxxx",
                        lines=1,
                        type="password",
                    )
                with gr.Column(scale=1):
                    pass
            with gr.Row():
                # spacer, centered button, spacer
                with gr.Column(scale=1):
                    pass
                with gr.Column(scale=0, min_width=220):
                    play_btn = gr.Button("Play", variant="primary")
                with gr.Column(scale=1):
                    pass
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
                gr.Markdown("OR")
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
                with gr.Row():
                    with gr.Column(scale=1):
                        pass
                    with gr.Column(scale=0, min_width=220):
                        generate_ak_btn = gr.Button("Generate New Access Token", variant="secondary")
                    with gr.Column(scale=1):
                        pass
        gate_msg = gr.Markdown("", visible=True)

        main = gr.Group(visible=False)
        with main:
            # Setup + instructions panels
            instructions_md = gr.Markdown("")

            # Opening scene
            opening_md = gr.Markdown("")

            # Chat (messages API)
            chat = gr.Chatbot(label="Chat", height=400, type="messages")
            with gr.Row(equal_height=True):
                with gr.Column(scale=8):
                    user_box = gr.Textbox(
                        show_label=False,
                        placeholder="What do you do next?",
                    )
                with gr.Column(scale=1):
                    # TODO: why is this not centered vertically with the textbox?
                    send_btn = gr.Button("Send")

            # Polling timer to check for new messages from simulation engine
            timer = gr.Timer(2, active=True)

            # Wiring
            send_btn.click(on_send, [user_box, chat, state], [chat, user_box])
            user_box.submit(on_send, [user_box, chat, state], [chat, user_box])
            # include `timer` in outputs and return a `gr.update(every=None)` to stop
            timer.tick(poll_fn, inputs=[chat, state], outputs=[chat, state, timer])

        results = gr.Group(visible=False)
        with results:
            # TODO: display simulation results
            pass

        # Wiring
        play_btn.click(
            _enter_play,
            [state],
            [state, ungated_landing, main, mode_md],
        ).then(  # <-- run loader next and show a progress bar
            load_with_progress,
            [state],
            [instructions_md, opening_md, state, chat],
        )
        generate_ak_btn.click(
            _get_player_id_from_token,
            [token_box, state],
            [state, gated_landing, main, gate_msg, mode_md],
        ).then(
            load_with_progress,
            [state],
            [instructions_md, opening_md, state, chat],
        )

    return app


def _enter_play(
    state: AppState,
) -> Tuple[AppState, gr.update, gr.update, gr.update]:
    state["access_token"] = None

    # hide gates, show main
    return (
        state,
        gr.update(visible=False),  # gate
        gr.update(visible=True),  # main
    )

def _create_access_token() -> str:
    """Create a new access token."""
    # display consent form

def _get_player_id_from_token(
    token: str, state: AppState
) -> Tuple[AppState, gr.update, gr.update, gr.update, gr.update]:
    state["access_token"] = token

    # TODO: try to get player_id from access token

    # hide gates, show main
    return (
        state,
        gr.update(visible=False),  # gate
        gr.update(visible=True),  # main
        gr.update(value=""),  # clear gate message
    )

def load_with_progress(
    state: AppState, progress: gr.Progress = gr.Progress(track_tqdm=True)
) -> Tuple[gr.update, gr.update, AppState, gr.update]:
    """Load the simulation while displaying a progress bar.

    Args:
        state: Current application state.
        progress: A gr.Progress instance used to report progress.

    Returns:
        A tuple of Gradio updates and the updated state:
            (instructions_md, opening_md, new_state, chat_update)
    """
    progress(0, desc="Initializing")
    time.sleep(0.2)

    progress(0.4, desc="Loading simulation")
    instructions_md, opening_md, new_state, chat = on_load(state)

    progress(0.85, desc="Finalizing")
    time.sleep(0.2)

    progress(1.0, desc="Ready")
    return instructions_md, opening_md, new_state, chat
