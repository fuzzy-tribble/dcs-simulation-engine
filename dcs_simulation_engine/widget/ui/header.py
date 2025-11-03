"""Header UI for the DCS Simulation Engine widget."""
from typing import NamedTuple
import gradio as gr

from dcs_simulation_engine.core.game_config import GameConfig

class HeaderUI(NamedTuple):
    pass # no fields

def build_header(game_config: GameConfig) -> HeaderUI:
    gr.HTML('<div style="text-align:center" id="banner">🚧 <b>W.I.P.</b> This app is a work in progress. 🚧</div>')
    gr.Markdown(
        f"""
        <div style='text-align:center'>
          <h1 style='margin-bottom:0'>{game_config.name.title()}</h1>
          <p style='margin-top:6px;color:#666'>A DCS Simulation Engine Game</p>
        </div>
        """
    )
    return HeaderUI()