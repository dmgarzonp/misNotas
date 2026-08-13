"""Main entry point for Mis Apuntes application.

Initializes Qt application, high-DPI display attributes, SQLite database repository,
view window, controller, and QuickNoteManager system tray integration.
"""

import logging
import os
import sys
import traceback
from PyQt6.QtCore import QStandardPaths, Qt, QT_VERSION_STR
from PyQt6.QtWidgets import QApplication

from src.controllers.note_controller import NoteController
from src.models.note_model import NoteRepository, get_app_data_dir
from src.services.autostart_service import AutostartService
from src.services.global_shortcut import QuickNoteManager
from src.services.single_instance import SingleInstanceGuard
from src.views.note_window import NoteWindow

# Setup Persistent Logging to File & Console (~/.local/share/misNotas/mis_apuntes.log)
log_dir = get_app_data_dir()
log_file_path = os.path.join(log_dir, "mis_apuntes.log")


file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

logger = logging.getLogger("mis_apuntes")


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    """Global exception hook to capture unhandled errors into mis_apuntes.log."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical(
        "Excepción NO capturada al ejecutar Mis Apuntes:",
        exc_info=(exc_type, exc_value, exc_traceback),
    )


sys.excepthook = handle_uncaught_exception


def main() -> None:
    """Bootstraps and launches Mis Apuntes application."""
    logger.info("==================================================")
    logger.info("Iniciando aplicación Mis Apuntes v1.0.0...")
    logger.info("Log de diagnóstico guardado en: %s", log_file_path)
    logger.info("Python: %s", sys.version)
    logger.info("Qt version: %s", QT_VERSION_STR)
    logger.info("Ejecutable: %s", sys.executable)
    logger.info("Argumentos: %s", sys.argv)
    logger.info("==================================================")

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Mis Apuntes")
        app.setOrganizationName("ProyectosAI")
        app.setDesktopFileName("mis-apuntes.desktop")
        app.setQuitOnLastWindowClosed(False)  # Keep running in system tray

        # Single Instance Check
        single_instance_guard = SingleInstanceGuard()
        if single_instance_guard.is_another_instance_running():
            logger.info(
                "Otra instancia de Mis Apuntes ya está en ejecución. Enfocando notas existentes y saliendo..."
            )
            sys.exit(0)

        # Enable Autostart Service on OS Boot & Login
        autostart = AutostartService()
        autostart.enable_autostart()

        # Initialize System Tray Manager
        tray_manager = QuickNoteManager(app)
        app.setWindowIcon(tray_manager._create_note_icon())

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

        # Start single instance server with activation callback
        single_instance_guard.start_server(show_and_activate)

        tray_manager.show_main_requested.connect(show_and_activate)

        def on_about_to_quit():
            logger.info("Guardando estado de todas las notas antes de salir...")
            for ctrl in list(NoteController._active_controllers):
                try:
                    ctrl.save_timer.stop()
                    ctrl._save_current_note()
                except Exception as e:
                    logger.error("Error guardando nota al salir: %s", e)

        app.aboutToQuit.connect(on_about_to_quit)

        # Show Main Window on Startup
        show_and_activate()
        logger.info("Aplicación iniciada y lista.")

        sys.exit(app.exec())
    except Exception as e:
        logger.critical("Error fatal durante la inicialización: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

