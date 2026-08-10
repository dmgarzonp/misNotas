"""Main entry point for Mis Apuntes application.

Initializes Qt application, high-DPI display attributes, SQLite database repository,
view window, controller, and QuickNoteManager system tray integration.
"""

import logging
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from src.controllers.note_controller import NoteController
from src.models.note_model import NoteRepository
from src.services.global_shortcut import QuickNoteManager
from src.views.note_window import NoteWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("mis_apuntes")


def main() -> None:
    """Bootstraps and launches Mis Apuntes application."""
    logger.info("Iniciando aplicación Mis Apuntes...")
    app = QApplication(sys.argv)
    app.setApplicationName("Mis Apuntes")
    app.setOrganizationName("ProyectosAI")
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

    # Initialize System Tray Manager
    tray_manager = QuickNoteManager(app)

    # Initialize MVC Stack
    repository = NoteRepository()
    view = NoteWindow()
    controller = NoteController(
        view=view, repository=repository, tray_manager=tray_manager
    )

    def show_and_activate():
        view.show()
        view.raise_()
        view.activateWindow()

    tray_manager.show_main_requested.connect(show_and_activate)

    # Show Main Window on Startup
    show_and_activate()
    logger.info("Aplicación iniciada y lista.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
