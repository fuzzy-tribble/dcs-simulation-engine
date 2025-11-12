"""Wiring of event handlers to widget components."""

import gradio as gr

from dcs_simulation_engine.widget.handlers import (
    handle_chat_feedback,
    on_consent_submit,
    on_gate_continue,
    setup_simulation,
)
from dcs_simulation_engine.widget.ui.chat import ChatUI
from dcs_simulation_engine.widget.ui.consent import ConsentUI
from dcs_simulation_engine.widget.ui.game_setup import GameSetupUI
from dcs_simulation_engine.widget.ui.gate import GateUI


def wire_handlers(
    state: gr.State,
    gate: GateUI,
    consent: ConsentUI,
    game_setup: GameSetupUI,
    chat: ChatUI,
) -> None:
    """Wire event handlers to widget components."""
    # Note: Chat handlers are wired in ChatUI build function as args of gr.ChatInterface

    # Wire game setup
    setup_sim_evt = game_setup.play_btn.click(
        # show chat view
        fn=lambda: [
            gr.update(visible=False),  # hide game setup
            gr.update(visible=True),  # show chat container
            gr.update(visible=False),  # disable chat textbox initially
        ],
        inputs=[],
        outputs=[
            game_setup.container,
            chat.container,
            chat.interface.textbox,
        ],
    ).success(
        fn=setup_simulation,
        inputs=[state, game_setup.pc_dropdown, game_setup.npc_dropdown],
        outputs=[state, chat.interface.chatbot_value],
    )

    setup_sim_evt.success(
        fn=lambda: gr.update(visible=True),  # renable chat textbox
        inputs=[],
        outputs=[chat.interface.textbox],
    )
    setup_sim_evt.failure(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[chat.container],
    )

    # Wire chat feedback
    chat.interface.chatbot.like(
        fn=handle_chat_feedback,
        inputs=[state],
        outputs=[],
    )

    # Wire gate page if present
    gate.continue_btn.click(
        fn=on_gate_continue,
        inputs=[
            state,
            gate.token_box,  # token value input
        ],
        outputs=[
            state,
            gate.container,
            game_setup.container,
            game_setup.pc_dropdown,
            game_setup.npc_dropdown,
            gate.token_box,
            gate.token_error_box,
        ],
    ).failure(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[gate.container],
    )

    # Wire gate generate token button
    gate.generate_token_btn.click(
        fn=lambda: [
            gr.update(visible=False),  # hide gate
            gr.update(visible=True),  # show consent
            gr.update(value=""),  # clear token box
            gr.update(visible=False, value=""),  # clear token error box
        ],
        inputs=[],
        outputs=[
            gate.container,
            consent.form_group,
            gate.token_box,
            gate.token_error_box,
        ],
    )

    # Wire consent page handlers
    consent.submit_btn.click(
        fn=on_consent_submit,
        inputs=[
            state,
            gr.State(list(consent.fields.keys())),
            *consent.fields.values(),
        ],
        outputs=[
            state,
            consent.form_group,
            consent.token_group,
            consent.token_text,
            gate.token_error_box,
        ],
    ).failure(
        fn=lambda: gr.update(visible=False),
        inputs=[],
        outputs=[consent.form_group],
    )

    consent.token_continue_btn.click(
        fn=lambda: [
            gr.update(visible=True),  # show gate
            gr.update(visible=False),  # hide consent form
            gr.update(visible=False),  # hide token group
            # IMPORTANT: clear token display to avoid leaking tokens
            gr.update(placeholder=""),  # clear token display
        ],
        inputs=[],
        outputs=[
            gate.container,
            consent.form_group,
            consent.token_group,
            consent.token_text,
        ],
    )
