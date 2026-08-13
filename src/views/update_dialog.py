"""Update Dialog Component for Mis Apuntes application.

Provides a modern macOS/GNOME styled modal dialog with an animated spinner
to inform users about software update progress and results.
"""

import logging
from typing import Optional
from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.services.update_service import CURRENT_VERSION
from src.views.styles import PASTEL_THEMES, get_gnome_icon

logger = logging.getLogger("mis_apuntes.update_dialog")


class UpdateDialog(QDialog):
    """Modal dialog displaying update checking progress, results, or error messages."""

    retry_requested = pyqtSignal()

    def __init__(
        self, parent: Optional[QWidget] = None, current_version: str = CURRENT_VERSION
    ) -> None:
        super().__init__(parent)
        self.current_version = current_version
        self.download_url: Optional[str] = None

        self.setWindowTitle("Actualizaciones de Software")
        self.setFixedSize(380, 220)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)

        self._setup_ui()
        self._apply_styles()
        self.set_searching()

    def _setup_ui(self) -> None:
        """Constructs UI layout elements."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header with Icon & Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setScaledContents(True)
        header_layout.addWidget(self.icon_label)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        self.title_label = QLabel("Buscar Actualizaciones", self)
        self.title_label.setObjectName("DialogTitle")

        self.subtitle_label = QLabel(f"Versión actual: v{self.current_version}", self)
        self.subtitle_label.setObjectName("DialogSubtitle")

        title_container.addWidget(self.title_label)
        title_container.addWidget(self.subtitle_label)
        header_layout.addLayout(title_container)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Status Message Description
        self.status_label = QLabel("Comprobando el servidor...", self)
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Animated Indeterminate Progress Bar (Spinner replacement)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Pulse animation
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        layout.addWidget(self.progress_bar)

        # Action Buttons Layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.addStretch()

        self.retry_button = QPushButton("Reintentar", self)
        self.retry_button.setObjectName("SecondaryButton")
        self.retry_button.clicked.connect(self._on_retry_clicked)
        self.retry_button.hide()
        self.button_layout.addWidget(self.retry_button)

        self.action_button = QPushButton("Descargar e Instalar", self)
        self.action_button.setObjectName("PrimaryButton")
        self.action_button.clicked.connect(self._on_action_clicked)
        self.action_button.hide()
        self.button_layout.addWidget(self.action_button)

        self.close_button = QPushButton("Cerrar", self)
        self.close_button.setObjectName("SecondaryButton")
        self.close_button.clicked.connect(self.accept)
        self.button_layout.addWidget(self.close_button)

        layout.addLayout(self.button_layout)

    def _apply_styles(self) -> None:
        """Applies Sequoia pastel styling rules to dialog widgets."""
        theme = PASTEL_THEMES["honey"]
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {theme.background};
                border-radius: 12px;
            }}
            #DialogTitle {{
                font-family: 'Inter', sans-serif;
                font-size: 15px;
                font-weight: 700;
                color: {theme.text_color};
            }}
            #DialogSubtitle {{
                font-family: 'Inter', sans-serif;
                font-size: 12px;
                color: {theme.muted_text};
            }}
            #StatusLabel {{
                font-family: 'Inter', sans-serif;
                font-size: 13px;
                color: {theme.text_color};
            }}
            QProgressBar {{
                background-color: {theme.border};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {theme.accent};
                border-radius: 4px;
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
                font-size: 13px;
                padding: 6px 14px;
            }}
            #SecondaryButton:hover {{
                background-color: {theme.button_hover};
            }}
            """)

    def set_searching(self) -> None:
        """Sets UI state to active searching with animated progress pulse."""
        icon = get_gnome_icon("software-update-available-symbolic")
        if icon.isNull():
            icon = QIcon.fromTheme("system-software-update-symbolic")
        self.icon_label.setPixmap(icon.pixmap(40, 40))

        self.title_label.setText("Buscando Actualizaciones")
        self.status_label.setText("Conectando con el servidor de actualizaciones...")
        self.progress_bar.show()
        self.retry_button.hide()
        self.action_button.hide()
        self.close_button.setText("Cancelar")

    def set_update_found(self, latest_version: str, html_url: str) -> None:
        """Sets UI state when a new release is available."""
        self.download_url = html_url
        icon = get_gnome_icon("software-update-available-symbolic")
        self.icon_label.setPixmap(icon.pixmap(40, 40))

        self.title_label.setText("¡Nueva Actualización Disponible!")
        self.status_label.setText(
            f"La versión <b>v{latest_version}</b> ya está disponible para descargar."
        )
        self.progress_bar.hide()
        self.retry_button.hide()
        self.action_button.show()
        self.close_button.setText("Más tarde")

    def set_up_to_date(self) -> None:
        """Sets UI state when application is at latest release."""
        icon = get_gnome_icon("emblem-ok-symbolic")
        if icon.isNull():
            icon = get_gnome_icon("object-select-symbolic")
        self.icon_label.setPixmap(icon.pixmap(40, 40))

        self.title_label.setText("Mis Apuntes está Actualizado")
        self.status_label.setText(
            f"Tienes instalada la versión más reciente (<b>v{self.current_version}</b>)."
        )
        self.progress_bar.hide()
        self.retry_button.hide()
        self.action_button.hide()
        self.close_button.setText("Aceptar")

    def set_error(self, err_msg: str) -> None:
        """Sets UI state when network error or timeout occurs during check."""
        icon = get_gnome_icon("dialog-error-symbolic")
        self.icon_label.setPixmap(icon.pixmap(40, 40))

        self.title_label.setText("Error de Verificación")
        clean_msg = (
            "No se pudo conectar con el servidor de actualizaciones."
            if "HTTP" in err_msg or "URL" in err_msg or "timed out" in err_msg
            else err_msg
        )
        self.status_label.setText(f"{clean_msg}\nVerifica tu conexión a internet.")
        self.progress_bar.hide()
        self.retry_button.show()
        self.action_button.hide()
        self.close_button.setText("Cerrar")

    def _on_action_clicked(self) -> None:
        """Opens download page in default browser and accepts dialog."""
        if self.download_url:
            QDesktopServices.openUrl(QUrl(self.download_url))
        self.accept()

    def _on_retry_clicked(self) -> None:
        """Triggers retry signal and resets dialog to searching state."""
        self.set_searching()
        self.retry_requested.emit()
