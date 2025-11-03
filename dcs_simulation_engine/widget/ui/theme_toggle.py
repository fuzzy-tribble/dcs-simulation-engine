# ui/theme_toggle.py
from typing import NamedTuple
import gradio as gr

class ThemeToggleUI(NamedTuple):
    toggle_btn: gr.Button

def build_theme_toggle() -> ThemeToggleUI:
    gr.HTML("""
        <style>
          #theme-toggle{position:absolute;top:10px;right:10px;z-index:999;background:#444;color:#fff;border-radius:50%;
          width:40px;height:40px;text-align:center;line-height:40px;cursor:pointer;font-size:18px;border:none;}
          #theme-toggle:hover{background:#666;}
        </style>
    """)
    toggle_btn = gr.Button("🌗", elem_id="theme-toggle")
    return ThemeToggleUI(toggle_btn=toggle_btn)