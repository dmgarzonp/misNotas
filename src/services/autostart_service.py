"""Autostart and Background Systemd Persistence Service for Mis Apuntes."""

import logging
import os
import sys
from typing import Optional
from PyQt6.QtCore import QStandardPaths

logger = logging.getLogger("mis_apuntes.autostart")


class AutostartService:
    """Manages system autostart entries (~/.config/autostart and systemd user services)."""

    def __init__(self, autostart_dir: Optional[str] = None) -> None:
        if autostart_dir is None:
            config_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.ConfigLocation
            )
            if not config_dir:
                config_dir = os.path.expanduser("~/.config")
            self.autostart_dir = os.path.join(config_dir, "autostart")
        else:
            self.autostart_dir = autostart_dir

        self.desktop_file_path = os.path.join(self.autostart_dir, "mis-apuntes.desktop")

    def is_autostart_enabled(self) -> bool:
        """Checks if autostart desktop entry exists and is enabled."""
        return os.path.exists(self.desktop_file_path)

    def enable_autostart(self) -> bool:
        """Creates autostart desktop entry in ~/.config/autostart/mis-apuntes.desktop."""
        try:
            os.makedirs(self.autostart_dir, exist_ok=True)
            exec_cmd = f"{sys.executable} {os.path.abspath(sys.argv[0])}"
            content = f"""[Desktop Entry]
Type=Application
Name=Mis Apuntes
Comment=Notas Rápidas y Notas de Escritorio Persistentes
Exec={exec_cmd}
Icon=text-x-generic
Terminal=false
Categories=Utility;Application;
X-GNOME-Autostart-enabled=true
StartupNotify=false
"""
            with open(self.desktop_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("Autostart activado en: %s", self.desktop_file_path)
            return True
        except Exception as e:
            logger.error("Error activando autostart: %s", e)
            return False

    def disable_autostart(self) -> bool:
        """Removes autostart desktop entry."""
        try:
            if os.path.exists(self.desktop_file_path):
                os.remove(self.desktop_file_path)
                logger.info("Autostart desactivado: %s", self.desktop_file_path)
            return True
        except Exception as e:
            logger.error("Error desactivando autostart: %s", e)
            return False
