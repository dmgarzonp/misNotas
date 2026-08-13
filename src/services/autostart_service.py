"""Autostart and Background Systemd Persistence Service for Mis Apuntes."""

import logging
import os
import sys
from typing import Optional
from PyQt6.QtCore import QStandardPaths

logger = logging.getLogger("mis_apuntes.autostart")


class AutostartService:
    """Manages system autostart entries (~/.config/autostart and systemd user services)."""

    def __init__(
        self,
        autostart_dir: Optional[str] = None,
        systemd_user_dir: Optional[str] = None,
    ) -> None:
        config_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.ConfigLocation
        )
        if not config_dir:
            config_dir = os.path.expanduser("~/.config")

        if autostart_dir is None:
            self.autostart_dir = os.path.join(config_dir, "autostart")
        else:
            self.autostart_dir = autostart_dir

        self.desktop_file_path = os.path.join(self.autostart_dir, "mis-apuntes.desktop")

        if systemd_user_dir is None:
            self.systemd_user_dir = os.path.join(config_dir, "systemd", "user")
        else:
            self.systemd_user_dir = systemd_user_dir

        self.systemd_service_path = os.path.join(
            self.systemd_user_dir, "mis-apuntes.service"
        )

    def _resolve_executable_command(self) -> tuple[str, str]:
        """Resolves executable path and working directory for autostart."""
        main_script = os.path.abspath(sys.argv[0])
        work_dir = os.path.dirname(main_script)

        if os.path.exists("/usr/bin/MisApuntes"):
            return "/usr/bin/MisApuntes", "/usr/bin"
        elif os.path.exists("/usr/bin/mis-apuntes"):
            return "/usr/bin/mis-apuntes", "/usr/bin"
        elif os.path.exists("/usr/local/bin/mis-apuntes"):
            return "/usr/local/bin/mis-apuntes", "/usr/local/bin"
        else:
            return f"{sys.executable} {main_script}", work_dir

    def is_autostart_enabled(self) -> bool:
        """Checks if autostart desktop entry or systemd service exists and is enabled."""
        return os.path.exists(self.desktop_file_path) or os.path.exists(
            self.systemd_service_path
        )

    def enable_autostart(self) -> bool:
        """Creates autostart desktop entry in ~/.config/autostart/mis-apuntes.desktop and systemd user service."""
        success = True
        exec_cmd, work_dir = self._resolve_executable_command()

        # 1. XDG Autostart Desktop Entry
        try:
            os.makedirs(self.autostart_dir, exist_ok=True)
            content = f"""[Desktop Entry]
Type=Application
Name=Mis Apuntes
Comment=Notas Rápidas y Notas de Escritorio Persistentes
Exec={exec_cmd}
Path={work_dir}
Icon=mis-apuntes
Terminal=false
Categories=Utility;Application;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=2
StartupNotify=false
"""
            with open(self.desktop_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("XDG Autostart activado en: %s", self.desktop_file_path)
        except Exception as e:
            logger.error("Error activando XDG autostart: %s", e)
            success = False

        # 2. Systemd User Service Unit
        try:
            os.makedirs(self.systemd_user_dir, exist_ok=True)
            service_content = f"""[Unit]
Description=Mis Apuntes Background & Desktop Notes Service
After=graphical-session.target

[Service]
Type=simple
ExecStart={exec_cmd}
WorkingDirectory={work_dir}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""
            with open(self.systemd_service_path, "w", encoding="utf-8") as f:
                f.write(service_content)
            logger.info("Systemd user service creado en: %s", self.systemd_service_path)
        except Exception as e:
            logger.warning("No se pudo crear el servicio systemd user: %s", e)

        return success

    def disable_autostart(self) -> bool:
        """Removes autostart desktop entry and systemd user service."""
        try:
            if os.path.exists(self.desktop_file_path):
                os.remove(self.desktop_file_path)
                logger.info("XDG Autostart desactivado: %s", self.desktop_file_path)
            if os.path.exists(self.systemd_service_path):
                os.remove(self.systemd_service_path)
                logger.info("Systemd service desactivado: %s", self.systemd_service_path)
            return True
        except Exception as e:
            logger.error("Error desactivando autostart: %s", e)
            return False

