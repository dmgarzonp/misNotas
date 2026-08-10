"""Interfaces package for Mis Apuntes application."""

from src.interfaces.note_repository import INoteRepository
from src.interfaces.services import IAuthService, IImageManager

__all__ = ["INoteRepository", "IAuthService", "IImageManager"]
