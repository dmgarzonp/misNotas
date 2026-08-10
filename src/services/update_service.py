"""Application Update Service using QThread and GitHub Releases API."""

import json
import logging
import urllib.request
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("mis_apuntes.update")

CURRENT_VERSION = "1.0.0"
GITHUB_RELEASES_URL = "https://api.github.com/repos/dmgarzonp/misNotas/releases/latest"


class UpdateWorker(QThread):
    """Background worker checking GitHub Releases API without blocking UI."""

    update_found = pyqtSignal(str, str)  # latest_version, html_url
    up_to_date = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, current_version: str = CURRENT_VERSION) -> None:
        super().__init__()
        self.current_version = current_version

    def run(self) -> None:
        """Executes HTTP request to GitHub API in background thread."""
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_URL,
                headers={"User-Agent": "MisApuntes-UpdateChecker/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "").lstrip("v").strip()
                    html_url = data.get(
                        "html_url", "https://github.com/dmgarzonp/misNotas"
                    )

                    if tag_name and self._is_newer_version(
                        tag_name, self.current_version
                    ):
                        self.update_found.emit(tag_name, html_url)
                    else:
                        self.up_to_date.emit()
                else:
                    self.error_occurred.emit(f"HTTP Status {response.status}")
        except Exception as e:
            logger.warning("No se pudo verificar actualizaciones: %s", e)
            self.error_occurred.emit(str(e))

    @staticmethod
    def _is_newer_version(latest: str, current: str) -> bool:
        """Compares semantic version strings (e.g. 1.1.0 vs 1.0.0)."""
        try:
            latest_parts = [int(p) for p in latest.split(".") if p.isdigit()]
            current_parts = [int(p) for p in current.split(".") if p.isdigit()]
            return latest_parts > current_parts
        except Exception:
            return False


class UpdateService:
    """Manages update worker lifecycle."""

    def __init__(self, current_version: str = CURRENT_VERSION) -> None:
        self.current_version = current_version
        self._worker: Optional[UpdateWorker] = None

    def check_for_updates(self, on_found, on_up_to_date, on_error) -> None:
        """Launches background update worker and attaches callbacks."""
        self._worker = UpdateWorker(current_version=self.current_version)
        self._worker.update_found.connect(on_found)
        self._worker.up_to_date.connect(on_up_to_date)
        self._worker.error_occurred.connect(on_error)
        self._worker.start()
