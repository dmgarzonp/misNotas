"""Single instance guard service for Mis Apuntes application using QLocalServer & QLocalSocket.

Ensures that only one instance of Mis Apuntes runs at any time. When a second instance
is launched, it notifies the existing running instance via QLocalSocket IPC to raise and
focus its note windows, then exits cleanly.
"""

import logging
from typing import Callable, Optional
from PyQt6.QtCore import QObject
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

logger = logging.getLogger("mis_apuntes.single_instance")

DEFAULT_SOCKET_NAME = "mis_apuntes_single_instance_socket"


class SingleInstanceGuard(QObject):
    """Guards application against duplicate running instances via local domain socket."""

    def __init__(
        self, socket_name: str = DEFAULT_SOCKET_NAME, parent: Optional[QObject] = None
    ) -> None:
        super().__init__(parent)
        self.socket_name = socket_name
        self.server: Optional[QLocalServer] = None
        self._on_activate_callback: Optional[Callable[[], None]] = None

    def is_another_instance_running(self) -> bool:
        """Checks if a primary instance is already running by attempting socket connection."""
        socket = QLocalSocket(self)
        socket.connectToServer(self.socket_name)
        if socket.waitForConnected(500):
            logger.info(
                "Otra instancia de Mis Apuntes ya está ejecutándose. Enviando señal de enfoque..."
            )
            socket.write(b"ACTIVATE")
            socket.flush()
            socket.disconnectFromServer()
            return True
        return False

    def start_server(self, on_activate_callback: Callable[[], None]) -> bool:
        """Starts local server listening for activation signals from secondary instances."""
        self._on_activate_callback = on_activate_callback

        # Clean up stale socket file from previous abnormal process termination/crash
        QLocalServer.removeServer(self.socket_name)

        self.server = QLocalServer(self)
        if not self.server.listen(self.socket_name):
            logger.error(
                "No se pudo iniciar el servidor de instancia única en %s: %s",
                self.socket_name,
                self.server.errorString(),
            )
            return False

        self.server.newConnection.connect(self._handle_new_connection)
        logger.info(
            "Servidor de instancia única iniciado escuchando en '%s'.", self.socket_name
        )
        return True

    def _handle_new_connection(self) -> None:
        """Handles incoming socket connection from secondary instance."""
        if not self.server:
            return
        client_socket = self.server.nextPendingConnection()
        if client_socket:
            if client_socket.waitForReadyRead(500):
                msg = client_socket.readAll().data().decode("utf-8", errors="replace")
                logger.info(
                    "Señal recibida de segunda instancia ('%s'). Enfocando notas...", msg
                )
            else:
                logger.info("Nueva conexión recibida. Enfocando notas...")

            if self._on_activate_callback:
                self._on_activate_callback()

            client_socket.disconnectFromServer()
