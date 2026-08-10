"""Design System and Pastel Themes for Mis Apuntes application.

Provides curated macOS-inspired color palettes (Honey, Mint, Lavender, Cream),
QSS stylesheet generators, and GNOME symbolic icon helpers.
"""

from dataclasses import dataclass
from typing import Dict
from PyQt6.QtGui import QIcon


def get_gnome_icon(icon_name: str) -> QIcon:
    """Returns native GNOME symbolic QIcon or falls back to empty QIcon."""
    icon = QIcon.fromTheme(icon_name)
    if not icon.isNull():
        return icon
    return QIcon()


@dataclass
class PastelTheme:
    name: str
    display_name: str
    background: str
    border: str
    accent: str
    text_color: str
    muted_text: str
    button_hover: str
    line_color: str
    swatch_color: str
    swatch_darker: str


PASTEL_THEMES: Dict[str, PastelTheme] = {
    "honey": PastelTheme(
        name="honey",
        display_name="Miel 🍯",
        background="#FFF8E7",
        border="#F5DFB3",
        accent="#D97706",
        text_color="#452A03",
        muted_text="#92400E",
        button_hover="rgba(217, 119, 6, 0.12)",
        line_color="rgba(217, 119, 6, 0.16)",
        swatch_color="#FBBF24",
        swatch_darker="#B45309",
    ),
    "mint": PastelTheme(
        name="mint",
        display_name="Menta 🌿",
        background="#EDFDF5",
        border="#C3F4DE",
        accent="#059669",
        text_color="#064E3B",
        muted_text="#047857",
        button_hover="rgba(5, 150, 105, 0.12)",
        line_color="rgba(5, 150, 105, 0.16)",
        swatch_color="#34D399",
        swatch_darker="#047857",
    ),
    "lavender": PastelTheme(
        name="lavender",
        display_name="Lavanda 🪻",
        background="#F6F4FE",
        border="#DDD6FE",
        accent="#7C3AED",
        text_color="#3B0764",
        muted_text="#6D28D9",
        button_hover="rgba(124, 58, 237, 0.12)",
        line_color="rgba(124, 58, 237, 0.16)",
        swatch_color="#A78BFA",
        swatch_darker="#6D28D9",
    ),
    "cream": PastelTheme(
        name="cream",
        display_name="Crema 🍨",
        background="#FAF9F6",
        border="#E7E5E4",
        accent="#78716C",
        text_color="#1C1917",
        muted_text="#57534E",
        button_hover="rgba(120, 113, 108, 0.12)",
        line_color="rgba(120, 113, 108, 0.16)",
        swatch_color="#A8A29E",
        swatch_darker="#44403C",
    ),
}


def get_theme(theme_name: str) -> PastelTheme:
    """Returns PastelTheme object or falls back to 'honey'."""
    return PASTEL_THEMES.get(theme_name.lower(), PASTEL_THEMES["honey"])


def get_window_qss(theme: PastelTheme) -> str:
    """Generates complete QSS stylesheet for NoteWindow using specified theme."""
    return f"""
    #ContainerWidget {{
        background-color: {theme.background};
        border: 1px solid {theme.border};
        border-radius: 18px;
    }}
    
    #TitleInput {{
        background: transparent;
        border: none;
        color: {theme.text_color};
        font-family: 'Inter', 'SF Pro Text', 'Roboto', sans-serif;
        font-size: 18px;
        font-weight: 700;
        padding: 14px 18px 4px 18px;
    }}
    
    #ContentEdit {{
        background: transparent;
        border: none;
        color: {theme.text_color};
        font-family: 'Inter', 'SF Pro Text', 'Roboto', sans-serif;
        font-size: 14px;
        padding: 8px 18px 14px 18px;
        selection-background-color: {theme.border};
        selection-color: {theme.text_color};
    }}

    #StatusBadge {{
        background-color: {theme.border};
        border-radius: 10px;
        color: {theme.text_color};
        font-size: 11px;
        font-weight: 600;
        padding: 3px 10px;
    }}

    QMenu {{
        background-color: {theme.background};
        border: 1px solid {theme.border};
        border-radius: 12px;
        padding: 6px;
    }}

    QMenu::item {{
        color: {theme.text_color};
        padding: 7px 18px;
        border-radius: 6px;
        font-family: 'Inter', 'SF Pro Text', 'Roboto', sans-serif;
        font-size: 13px;
    }}

    QMenu::item:selected {{
        background-color: {theme.button_hover};
        color: {theme.accent};
    }}

    QMenu::separator {{
        height: 1px;
        background: {theme.border};
        margin: 4px 8px;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 4px 2px 4px 2px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {theme.border};
        min-height: 20px;
        border-radius: 4px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {theme.accent};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QSizeGrip {{
        width: 16px;
        height: 16px;
        background: transparent;
    }}
    """
