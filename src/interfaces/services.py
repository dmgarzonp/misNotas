"""Abstract interfaces for application services (Authentication, Asset Management)."""

from abc import ABC, abstractmethod
from typing import Optional


class IAuthService(ABC):
    """Abstract contract for authentication and security services."""

    @abstractmethod
    def authenticate_user(self, reason_prompt: str = "Desbloquear nota") -> bool:
        """Authenticates user via PAM, Polkit or GUI password dialog."""
        pass


class IImageManager(ABC):
    """Abstract contract for image asset import and local storage."""

    @abstractmethod
    def import_image(self, source_path: str) -> Optional[str]:
        """Copies image to application assets storage and returns file URL."""
        pass
