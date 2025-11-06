"""Theme toggle UI component for switching between light and dark modes."""

from typing import NamedTuple

import gradio as gr


class ThemeToggleUI(NamedTuple):
    """Named tuple for theme toggle UI components."""

    toggle_btn: gr.Button


def build_theme_toggle() -> ThemeToggleUI:
    """Builds a theme toggle button for switching between light and dark modes."""
    gr.HTML(
        """
        <style>
          #theme-toggle{position:absolute;top:10px;right:10px;z-index:999;background:#444;color:#fff;border-radius:50%;
          width:40px;height:40px;text-align:center;line-height:40px;cursor:pointer;font-size:18px;border:none;}
          #theme-toggle:hover{background:#666;}
        </style>
    """
    )
    toggle_btn = gr.Button("🌗", elem_id="theme-toggle")
    return ThemeToggleUI(toggle_btn=toggle_btn)
