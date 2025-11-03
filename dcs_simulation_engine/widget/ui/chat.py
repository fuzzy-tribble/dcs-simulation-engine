"""Chat UI components."""
from typing import NamedTuple, Optional
import gradio as gr

class ChatUI(NamedTuple):
    container: gr.Group
    messages: gr.Chatbot
    user_input: gr.Textbox
    send_button: gr.Button

def build_chat() -> ChatUI:
    with gr.Group() as group:
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