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

# TODO: pre v001 - fix stopping and displaying performance table


def build_app() -> gr.Blocks:
    """Build the Gradio UI for running simulations."""
    with gr.Blocks(title="DCS Simulation Engine", theme=Soft()) as app:
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

        gr.Markdown(
            "<div style='text-align:center'>"
            "<h1 style='margin-bottom:0'>DCS Simulation Engine</h1>"
            "<p style='margin-top:6px;color:#666'>A text-based simulation engine for diverse types of cognitive systems.</p>"  # noqa: E501
            "</div>"
        )
        mode_md = gr.Markdown("", elem_id="run-mode", visible=False)

        state = gr.State(AppState())

        gate = gr.Group(visible=True)
        with gate:
            gr.Markdown(
                """
## Welcome

This is a research project under the Sonification Lab at GaTech. We are studying how well different types of cognitive systems can understand and infer the goals of another cognitive systems as their modalities of interaction diverge from the "norm".

## Instructions

To participate in our research, you’ll need to **sign a consent form** to receive an **access token**.  

With a token, you can start in **Benchmarking Mode**, which lets us collect **anonymous data** about your **goal-inference** capabilities for various types of cognitive systems in our simulations.  

Alternatively, you can try a **lower-fidelity Demo Mode** that lets you play around **without any data collection**.
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
                        label="Access Token",
                        placeholder="dcs-xxxx-xxxx-xxxx",
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
                    benchmark_btn = gr.Button("Begin Benchmarking", variant="primary")
                with gr.Column(scale=1):
                    pass
            with gr.Row():
                gr.Markdown("&nbsp;&nbsp;")  # empty row for spacing
            with gr.Row():
                # spacer, centered button, spacer
                with gr.Column(scale=1):
                    pass
                with gr.Column(scale=0, min_width=220):
                    demo_btn = gr.Button(
                        "or Continue in Demo Mode", variant="secondary"
                    )
                with gr.Column(scale=1):
                    pass

            gate_msg = gr.Markdown("", visible=True)

        main = gr.Group(visible=False)
        with main:
            # Load simulation button
            # TODO - replace with progress bar and auto-load on enter
            # with gr.Row():
            #     with gr.Column(scale=2):
            #         pass
            #     with gr.Column(scale=1):
            #         load_btn = gr.Button(
            #             "Load New Simulation", variant="primary", visible=True
            #         )
            #     with gr.Column(scale=2):
            #         pass

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
        demo_btn.click(
            _enter_demo,
            [state],
            [state, gate, main, mode_md],
        ).then(  # <-- run loader next and show a progress bar
            load_with_progress,
            [state],
            [instructions_md, opening_md, state, chat],
        )
        benchmark_btn.click(
            _enter_benchmark,
            [token_box, state],
            [state, gate, main, gate_msg, mode_md],
        ).then(
            load_with_progress,
            [state],
            [instructions_md, opening_md, state, chat],
        )

    return app


def _enter_demo(
    state: AppState,
) -> Tuple[AppState, gr.update, gr.update, gr.update]:
    state["mode"] = "demo"
    state["access_token"] = None

    # hide gate, show main
    return (
        state,
        gr.update(visible=False),  # gate
        gr.update(visible=True),  # main
        _render_mode(state),  # mode_md
    )


def _enter_benchmark(token: str, state: AppState) -> Tuple[AppState]:
    if not token.strip():
        # keep gate open, show a small message
        return (
            state,
            gr.update(visible=True),  # gate
            gr.update(visible=False),  # main
            "Please enter an access token.",  # gate_msg
            _render_mode(state),  # mode_md
        )
    state["mode"] = "benchmark"
    state["access_token"] = token.strip()
    return (
        state,
        gr.update(visible=False),
        gr.update(visible=True),
        "",
        _render_mode(state),
    )


def _render_mode(state: AppState) -> gr.update:
    """Render the run mode string below the title."""
    mode = state.get("mode")
    if not mode:
        return gr.update(visible=False)
    return gr.update(
        value=(
            "<p style='text-align:center;color:#888;font-size:0.9em'>"
            f"Run Mode: <strong>{mode.capitalize()}</strong>"
            "</p>"
        ),
        visible=True,
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
