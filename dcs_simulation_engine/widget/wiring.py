"""Wiring of event handlers to widget components."""

import gradio as gr

from dcs_simulation_engine.widget.handlers import (
    on_consent_submit,
    on_gate_continue,
    on_generate_token,
    on_play,
    on_send,
    on_token_continue,
)
from dcs_simulation_engine.widget.ui.chat import ChatUI
from dcs_simulation_engine.widget.ui.consent import ConsentUI
from dcs_simulation_engine.widget.ui.gate import GateUI
from dcs_simulation_engine.widget.ui.play import PlayUI


def wire_handlers(
    state: gr.State,
    gate: GateUI,
    consent: ConsentUI,
    play: PlayUI,
    chat: ChatUI,
) -> None:
    """Wire event handlers to widget components."""
    # Wire chat page handlers
    chat.send_btn.click(
        # wire send button
        fn=on_send,
        inputs=[state, chat.user_box, chat.events],
        outputs=[state, chat.user_box, chat.events],
    )
    chat.user_box.submit(
        # wire enter key in user input box
        fn=on_send,
        inputs=[state, chat.user_box, chat.events],
        outputs=[state, chat.user_box, chat.events],
    )

    # Wire play
    play.play_btn.click(
        fn=on_play,
        inputs=[state],
        outputs=[
            state,
            play.container,
            chat.container,
            chat.user_box,
            chat.send_btn,
            chat.loader,
        ],
    )

    # Wire gate page if present
    if gate:
        # Wire gate continue button
        gate.continue_btn.click(
            fn=on_gate_continue,
            inputs=[
                state,
                gate.token_box,  # token value input
            ],
            outputs=[
                state,
                gate.container,
                play.container,
                play.pc_dropdown,
                play.npc_dropdown,
                gate.token_box,
                gate.token_error_box,
            ],
        )

        # Wire gate generate token button
        if consent:
            gate.generate_token_btn.click(
                fn=on_generate_token,
                inputs=[state],
                outputs=[
                    state,
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
            )
            consent.token_continue_btn.click(
                fn=on_token_continue,
                inputs=[state],
                outputs=[
                    state,
                    gate.container,
                    consent.token_group,
                    consent.form_group,
                    consent.token_text,
                ],
            )
