"""Views package."""

from src.views.note_window import NoteWindow, TexturedTextEdit
from src.views.sidebar import SidebarWidget
from src.views.styles import PASTEL_THEMES, PastelTheme, get_theme, get_window_qss

__all__ = [
    "NoteWindow",
    "TexturedTextEdit",
    "SidebarWidget",
    "PastelTheme",
    "PASTEL_THEMES",
    "get_theme",
    "get_window_qss",
]
