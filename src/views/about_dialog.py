"""About Dialog Component for Mis Apuntes application.

Provides a modern Sequoia/GNOME styled modal displaying application details,
version v1.0.1, key features, author credits, and GitHub repository link.
"""

import logging
import os
from typing import Optional
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.update_service import CURRENT_VERSION
from src.views.styles import PASTEL_THEMES, get_gnome_icon

logger = logging.getLogger("mis_apuntes.about_dialog")


class AboutDialog(QDialog):
    """Modal dialog displaying application details, version v1.0.1, key features, and credits."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Acerca de Mis Apuntes")
        self.setFixedSize(430, 350)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Constructs About dialog UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header with Logo & Version
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel(self)
        icon_label.setFixedSize(52, 52)
        icon_label.setScaledContents(True)

        app_icon = QIcon.fromTheme("mis-apuntes")
        if app_icon.isNull():
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            svg_path = os.path.join(base_dir, "data", "mis-apuntes.svg")
            if os.path.exists(svg_path):
                app_icon = QIcon(svg_path)
            else:
                app_icon = get_gnome_icon("help-about-symbolic")

        icon_label.setPixmap(app_icon.pixmap(52, 52))
        header_layout.addWidget(icon_label)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Mis Apuntes", self)
        title.setObjectName("AboutTitle")

        subtitle = QLabel(f"Versión {CURRENT_VERSION} (Ubuntu Linux)", self)
        subtitle.setObjectName("AboutSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Description & Features List
        desc_label = QLabel(
            "<b>Aplicación de Notas Rápidas y Escritorio Persistente</b><br>"
            "Inspirada en la estética minimalista de Apple macOS Sequoia y la natividad de Ubuntu GNOME.<br><br>"
            "<b>Novedades destacadas en v1.0.1:</b><br>"
            "• 🛡️ <b>Instancia Única:</b> Evita ejecuciones duplicadas.<br>"
            "• 📍 <b>Posicionamiento Inteligente:</b> Restaura notas lado a lado.<br>"
            "• 🔄 <b>Actualizaciones en Vivo:</b> Descarga e instalación en vivo con feedback.<br>"
            "• 📌 <b>Integración AppIndicator:</b> Icono oficial en la barra superior de Ubuntu.",
            self,
        )
        desc_label.setObjectName("AboutDesc")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Footer with GitHub repository link & Close button
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        github_btn = QPushButton("🌐 Repositorio GitHub", self)
        github_btn.setObjectName("SecondaryButton")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://github.com/dmgarzonp/misNotas")
            )
        )

        close_btn = QPushButton("Cerrar", self)
        close_btn.setObjectName("PrimaryButton")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)

        footer_layout.addWidget(github_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(close_btn)

        layout.addLayout(footer_layout)

    def _apply_styles(self) -> None:
        """Applies Sequoia pastel stylesheet rules to About dialog."""
        theme = PASTEL_THEMES["honey"]
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.background};
                border-radius: 14px;
            }}
            #AboutTitle {{
                font-family: 'Inter', sans-serif;
                font-size: 18px;
                font-weight: 700;
                color: {theme.text_color};
            }}
            #AboutSubtitle {{
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                font-weight: 600;
                color: {theme.muted_text};
            }}
            #AboutDesc {{
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                line-height: 1.4;
                color: {theme.text_color};
            }}
            #PrimaryButton {{
                background-color: {theme.accent};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 16px;
            }}
            #PrimaryButton:hover {{
                background-color: {theme.swatch_darker};
            }}
            #SecondaryButton {{
                background-color: transparent;
                border: 1px solid {theme.border};
                color: {theme.text_color};
                border-radius: 8px;
                font-size: 12px;
                padding: 6px 14px;
            }}
            #SecondaryButton:hover {{
                background-color: {theme.button_hover};
            }}
            """)
