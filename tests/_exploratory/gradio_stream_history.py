# START
# Can stream with dict initial value? YES
# Can primt initial value with function? YES
import time

import gradio as gr

initial_history = [
    {"role": "assistant", "content": "#Welcome"},
    {"role": "assistant", "content": "Here is some initial content."},
]


def prime_chat_value():
    print("Priming chat value...")
    # return gr.update(value=initial_history)
    return initial_history


def slow_echo(message, history):
    out = ""
    if message is None:
        message = "a non empty message"
    for ch in message:
        out += ch
        time.sleep(0.05)  # slow down as you like
        yield out


with gr.Blocks() as demo:
    chatbot = gr.Chatbot(type="messages", value=[])
    chatinterface = gr.ChatInterface(
        fn=slow_echo,
        title="Slow Echo",
        chatbot=chatbot,
        type="messages",
    )
    demo.load(fn=prime_chat_value, inputs=None, outputs=[chatinterface.chatbot_value])

if __name__ == "__main__":
    demo.launch()
# END: TEST CAN STREAM

# can stream dicts?
