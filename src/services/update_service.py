"""Application Update Service using QThread and GitHub Releases API."""

import json
import logging
import ssl
import urllib.error
import urllib.request
from typing import Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("mis_apuntes.update")

CURRENT_VERSION = "1.0.1"
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
                headers={
                    "User-Agent": "MisApuntes-UpdateChecker/1.0",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            context = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    tag_name = data.get("tag_name", "").lstrip("v").strip()
                    html_url = data.get(
                        "html_url", "https://github.com/dmgarzonp/misNotas"
                    )

                    assets = data.get("assets", [])
                    deb_asset_url = None
                    for asset in assets:
                        asset_name = asset.get("name", "")
                        if asset_name.endswith(".deb"):
                            deb_asset_url = asset.get("browser_download_url")
                            break

                    download_url = deb_asset_url or html_url

                    if tag_name and self._is_newer_version(
                        tag_name, self.current_version
                    ):
                        self.update_found.emit(tag_name, download_url)
                    else:
                        self.up_to_date.emit()
                else:
                    self.error_occurred.emit(f"Respuesta HTTP {response.status}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                # 404 on /releases/latest means no releases published yet on GitHub repo
                logger.info(
                    "El repositorio de GitHub existe pero aún no tiene Releases publicadas (%s). Aplicación al día.",
                    e,
                )
                self.up_to_date.emit()
            else:
                logger.warning("Error HTTP al verificar actualizaciones: %s", e)
                self.error_occurred.emit(f"Error HTTP {e.code}")
        except urllib.error.URLError as e:
            logger.warning("No se pudo conectar con GitHub: %s", e)
            self.error_occurred.emit(
                "No se pudo conectar con el servidor de actualizaciones.\nVerifica tu conexión a internet."
            )
        except Exception as e:
            logger.warning("Error inesperado comprobando actualizaciones: %s", e)
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


class UpdateDownloaderWorker(QThread):
    """Background thread downloading .deb update package from GitHub Releases."""

    progress_updated = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    download_finished = pyqtSignal(str)  # local_file_path
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url: str) -> None:
        super().__init__()
        self.download_url = download_url

    def run(self) -> None:
        """Downloads file with progress signals."""
        import os

        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": "MisApuntes-UpdateChecker/1.0"},
            )
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=45, context=context) as response:
                total_size = int(response.headers.get("Content-Length", 0))

                target_dir = os.path.expanduser("~/.local/share/misNotas/updates")
                os.makedirs(target_dir, exist_ok=True)
                local_path = os.path.join(target_dir, "mis-apuntes_latest.deb")

                downloaded = 0
                chunk_size = 1024 * 64

                with open(local_path, "wb") as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress_updated.emit(downloaded, total_size)

                self.download_finished.emit(local_path)
        except Exception as e:
            logger.error("Error al descargar paquete de actualización: %s", e)
            self.error_occurred.emit(f"Error de descarga: {e}")


class UpdateInstallerWorker(QThread):
    """Background thread installing downloaded .deb package using pkexec graphical sudo."""

    install_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, deb_path: str) -> None:
        super().__init__()
        self.deb_path = deb_path

    def run(self) -> None:
        """Executes pkexec apt-get install in background thread."""
        import subprocess

        try:
            cmd = ["pkexec", "apt-get", "install", "-y", "--reinstall", self.deb_path]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                self.install_finished.emit()
            else:
                err_text = (
                    res.stderr.strip()
                    or res.stdout.strip()
                    or f"Código de salida {res.returncode}"
                )
                self.error_occurred.emit(err_text)
        except Exception as e:
            logger.error("Error al instalar paquete .deb: %s", e)
            self.error_occurred.emit(str(e))


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
