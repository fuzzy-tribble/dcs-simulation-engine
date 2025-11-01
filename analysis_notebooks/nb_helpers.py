# chat_helpers.py
import random
import gradio as gr
import queue


def play_gradio() -> str:
    """
    Blocking input provider for simulation.play(input_provider=...).
    Shows a Gradio chat UI; each call waits for the next user message.
    """
    if not hasattr(play_gradio, "_q"):
        play_gradio._q = queue.Queue()

        with gr.Blocks() as demo:
            chat = gr.Chatbot(label="Simulation")
            box = gr.Textbox(placeholder="Type a message…  (/quit to end)")

            def submit(msg, chat_history):
                chat_history = (chat_history or []) + [(msg, None)]
                play_gradio._q.put(msg)  # deliver to sim.play
                return "", chat_history  # clear textbox, update chat

            box.submit(submit, [box, chat], [box, chat])

        demo.launch()

    # Block until user types something in the Gradio box
    return play_gradio._q.get()


QUIT = {"/quit", "/exit", "/end"}


def random_number_chat(maxturns: int = 10):
    """
    Launch a simple Gradio chat that always replies with a random number.
    Ends after `maxturns` turns or if user types a quit command.
    """

    def respond(message, history, turns):
        message = (message or "").strip()
        if message.lower() in QUIT:
            reply = "Goodbye."
            disable = True
        else:
            reply = str(random.random())
            turns += 1
            disable = turns >= maxturns
            if disable:
                reply += "\n(Max turns reached. Ending.)"
        history = history + [(message, reply)]
        textbox_update = gr.update(
            value="",
            interactive=not disable,
            placeholder="Session ended." if disable else "",
        )
        return history, turns, textbox_update

    with gr.Blocks() as demo:
        chatbot = gr.Chatbot(label="Random-Number Chat")
        turns = gr.State(0)
        msg = gr.Textbox(placeholder="Type a message…  (/quit to end)")
        msg.submit(respond, [msg, chatbot, turns], [chatbot, turns, msg])

    return demo
