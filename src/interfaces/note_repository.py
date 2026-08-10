"""Abstract interface for Note repository persistence operations."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.models.note_model import Note


class INoteRepository(ABC):
    """Abstract Base Class defining the contract for note data persistence."""

    db_path: str

    @abstractmethod
    def create_note(
        self,
        title: str = "",
        content: str = "",
        content_html: str = "",
        theme: str = "honey",
        background_style: str = "blank",
        width: int = 300,
        height: int = 280,
    ) -> "Note":
        """Creates a new note entity."""
        pass

    @abstractmethod
    def get_note_by_id(self, note_id: int) -> Optional["Note"]:
        """Retrieves a note by its unique ID."""
        pass

    @abstractmethod
    def get_all_notes(self) -> List["Note"]:
        """Retrieves all notes ordered by pinned status and updated date."""
        pass

    @abstractmethod
    def update_note(
        self,
        note_id: int,
        title: str,
        content: str,
        content_html: str = "",
        theme: str = "honey",
        pinned: bool = False,
        is_locked: bool = False,
        background_style: str = "blank",
        width: int = 300,
        height: int = 280,
    ) -> Optional["Note"]:
        """Updates fields of an existing note."""
        pass

    @abstractmethod
    def toggle_pin(self, note_id: int) -> Optional["Note"]:
        """Toggles the pinned status of a note."""
        pass

    @abstractmethod
    def toggle_lock(self, note_id: int) -> Optional["Note"]:
        """Toggles the is_locked status of a note."""
        pass

    @abstractmethod
    def delete_note(self, note_id: int) -> bool:
        """Permanently deletes a note by ID."""
        pass

    @abstractmethod
    def search_notes(self, query: str) -> List["Note"]:
        """Searches notes by title or content substring."""
        pass

    @abstractmethod
    def get_notes_by_tag(self, tag: str) -> List["Note"]:
        """Filters notes containing specific hashtag."""
        pass
