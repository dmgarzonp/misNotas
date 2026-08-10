"""Sidebar View for Mis Apuntes application.

Provides macOS-styled expandable sidebar widget displaying pinned notes,
all notes list, search filter, and hashtag pills.
"""

from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models.note_model import Note
from src.views.styles import get_theme


class SidebarWidget(QWidget):
    """macOS-styled collapsible sidebar panel."""

    note_selected = pyqtSignal(int)
    tag_selected = pyqtSignal(str)
    search_changed = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)
        self._init_ui()

    def _init_ui(self) -> None:
        """Constructs sidebar UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header Title & Search
        header_layout = QHBoxLayout()
        title_label = QLabel("Apuntes", self)
        title_label.setStyleSheet("font-weight: 700; font-size: 14px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Search Input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("🔍 Buscar...")
        self.search_input.setStyleSheet(
            "border: 1px solid rgba(0, 0, 0, 0.15); border-radius: 6px; padding: 4px 8px; font-size: 12px;"
        )
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # Notes List
        self.pinned_label = QLabel("📌 FIJADAS", self)
        self.pinned_label.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #888; margin-top: 4px;"
        )
        layout.addWidget(self.pinned_label)

        self.notes_list = QListWidget(self)
        self.notes_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; font-size: 13px; }"
            "QListWidget::item { padding: 6px 8px; border-radius: 6px; margin-bottom: 2px; }"
            "QListWidget::item:hover { background-color: rgba(0, 0, 0, 0.05); }"
            "QListWidget::item:selected { background-color: rgba(0, 0, 0, 0.1); font-weight: 600; }"
        )
        self.notes_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.notes_list, 1)

        # Tags Section
        self.tags_label = QLabel("# ETIQUETAS", self)
        self.tags_label.setStyleSheet(
            "font-size: 10px; font-weight: 700; color: #888; margin-top: 4px;"
        )
        layout.addWidget(self.tags_label)

        self.tags_list = QListWidget(self)
        self.tags_list.setFixedHeight(100)
        self.tags_list.setStyleSheet(
            "QListWidget { background: transparent; border: none; font-size: 12px; }"
            "QListWidget::item { padding: 4px 6px; border-radius: 4px; color: #555; }"
            "QListWidget::item:hover { background-color: rgba(0, 0, 0, 0.05); color: #000; }"
        )
        self.tags_list.itemClicked.connect(self._on_tag_clicked)
        layout.addWidget(self.tags_list)

    def populate_notes(
        self, notes: List[Note], current_note_id: Optional[int] = None
    ) -> None:
        """Populates the notes list widget."""
        self.notes_list.clear()

        for note in notes:
            if note.id is None:
                continue

            icon = "📌 " if note.pinned else ("🔒 " if note.is_locked else "📝 ")
            title = note.display_title
            item = QListWidgetItem(f"{icon}{title}")
            item.setData(Qt.ItemDataRole.UserRole, note.id)

            self.notes_list.addItem(item)
            if current_note_id is not None and note.id == current_note_id:
                self.notes_list.setCurrentItem(item)

    def populate_tags(self, tags: List[str]) -> None:
        """Populates the tags list widget."""
        self.tags_list.clear()
        all_item = QListWidgetItem("Todas las notas")
        all_item.setData(Qt.ItemDataRole.UserRole, "")
        self.tags_list.addItem(all_item)

        for tag in sorted(tags):
            if tag:
                item = QListWidgetItem(f"#{tag}")
                item.setData(Qt.ItemDataRole.UserRole, tag)
                self.tags_list.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Emits note_selected signal when a note item is clicked."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        if note_id is not None:
            self.note_selected.emit(int(note_id))

    def _on_tag_clicked(self, item: QListWidgetItem) -> None:
        """Emits tag_selected signal when a tag item is clicked."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag is not None:
            self.tag_selected.emit(str(tag))
