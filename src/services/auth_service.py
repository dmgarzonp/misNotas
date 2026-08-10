"""System Authentication Service for Mis Apuntes application.

Triggers Ubuntu's native PolicyKit (pkexec) graphical authentication dialog
to authenticate the user via system credentials when accessing protected notes.
"""

import os
import subprocess
from typing import Optional
from src.interfaces.services import IAuthService


class AuthService(IAuthService):
    """Service providing system authentication using Ubuntu's native PolicyKit GUI dialog."""

    def __init__(self, override_auth: Optional[bool] = None) -> None:
        self.override_auth = override_auth

    def authenticate_user(
        self, reason_prompt: str = "Desbloquear Nota Protegida"
    ) -> bool:
        """Triggers native Ubuntu PolicyKit GUI password dialog using pkexec.

        Returns True if the user successfully enters their system password, False otherwise.
        """
        if self.override_auth is not None:
            return self.override_auth

        display = os.environ.get("DISPLAY", ":0")
        xauthority = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))

        try:
            # Execute pkexec true to invoke native GNOME PolicyKit dialog
            cmd = [
                "pkexec",
                "env",
                f"DISPLAY={display}",
                f"XAUTHORITY={xauthority}",
                "true",
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            return result.returncode == 0
        except Exception:
            return False
