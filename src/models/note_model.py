"""Model layer for Mis Apuntes application.

Implements Note entity dataclass and NoteRepository for thread-safe
SQLite persistence using WAL mode, atomic transactions, and auto-migrations.
"""

from dataclasses import dataclass, field
from datetime import datetime
import os
import re
import sqlite3
from typing import List, Optional, Set


@dataclass
class Note:
    """Represents a single note entity in the application with rich text & metadata."""

    id: Optional[int] = None
    title: str = ""
    content: str = ""
    content_html: str = ""
    theme: str = "honey"
    pinned: bool = False
    is_locked: bool = False
    tags: str = ""
    background_style: str = "blank"  # "blank", "ruled", "grid"
    created_at: str = ""
    updated_at: str = ""

    @property
    def display_title(self) -> str:
        """Returns non-empty title or falls back to first line of content."""
        if self.title.strip():
            return self.title.strip()
        lines = [line.strip() for line in self.content.splitlines() if line.strip()]
        if lines:
            first_line = lines[0]
            # Strip basic HTML tags if plain text content was derived from HTML
            clean_line = re.sub("<[^<]+?>", "", first_line).strip()
            return clean_line[:30] + ("..." if len(clean_line) > 30 else "")
        return "Nueva Nota"

    def extract_hashtags(self) -> Set[str]:
        """Extracts all #hashtags present in title or content."""
        text = f"{self.title} {self.content}"
        raw_tags = re.findall(r"#([\wñÑáéíóúÁÉÍÓÚ]+)", text)
        return {tag.lower() for tag in raw_tags}


class NoteRepository:
    """Thread-safe SQLite repository managing Note entities with WAL mode."""

    def __init__(self, db_path: str = "mis_apuntes.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Creates a SQLite connection configured with WAL journal mode."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init_db(self) -> None:
        """Initializes database schema and handles automatic column migrations."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    content_html TEXT NOT NULL DEFAULT '',
                    theme TEXT NOT NULL DEFAULT 'honey',
                    pinned INTEGER NOT NULL DEFAULT 0,
                    is_locked INTEGER NOT NULL DEFAULT 0,
                    tags TEXT NOT NULL DEFAULT '',
                    background_style TEXT NOT NULL DEFAULT 'blank',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """)
            conn.commit()

            # Ensure columns exist for existing databases (backward compatibility migration)
            cursor = conn.execute("PRAGMA table_info(notes);")
            columns = {row["name"] for row in cursor.fetchall()}
            migrations = [
                ("content_html", "TEXT NOT NULL DEFAULT ''"),
                ("is_locked", "INTEGER NOT NULL DEFAULT 0"),
                ("tags", "TEXT NOT NULL DEFAULT ''"),
                ("background_style", "TEXT NOT NULL DEFAULT 'blank'"),
            ]
            for col_name, col_type in migrations:
                if col_name not in columns:
                    conn.execute(f"ALTER TABLE notes ADD COLUMN {col_name} {col_type};")
            conn.commit()

    def _row_to_note(self, row: sqlite3.Row) -> Note:
        """Converts SQLite Row to Note dataclass instance."""
        return Note(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            content_html=row["content_html"] if "content_html" in row.keys() else "",
            theme=row["theme"],
            pinned=bool(row["pinned"]),
            is_locked=bool(row["is_locked"]) if "is_locked" in row.keys() else False,
            tags=row["tags"] if "tags" in row.keys() else "",
            background_style=(
                row["background_style"] if "background_style" in row.keys() else "blank"
            ),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get_all_notes(self) -> List[Note]:
        """Retrieves all notes ordered by pinned status and updated_at timestamp."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM notes ORDER BY pinned DESC, datetime(updated_at) DESC, id DESC;"
            )
            rows = cursor.fetchall()
            return [self._row_to_note(r) for r in rows]

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Fetches a single note by its primary key."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM notes WHERE id = ?;", (note_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_note(row)
            return None

    def create_note(
        self,
        title: str = "",
        content: str = "",
        content_html: str = "",
        theme: str = "honey",
        background_style: str = "blank",
    ) -> Note:
        """Creates and persists a new Note entity."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO notes (
                    title, content, content_html, theme, pinned, is_locked, tags, background_style, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 0, 0, '', ?, ?, ?);
                """,
                (
                    title,
                    content,
                    content_html,
                    theme,
                    background_style,
                    now,
                    now,
                ),
            )
            conn.commit()
            note_id = cursor.lastrowid
            note = Note(
                id=note_id,
                title=title,
                content=content,
                content_html=content_html,
                theme=theme,
                pinned=False,
                is_locked=False,
                tags="",
                background_style=background_style,
                created_at=now,
                updated_at=now,
            )

            # Extract tags and store
            extracted_tags = ",".join(sorted(note.extract_hashtags()))
            if extracted_tags:
                note.tags = extracted_tags
                conn.execute(
                    "UPDATE notes SET tags = ? WHERE id = ?;", (extracted_tags, note_id)
                )
                conn.commit()

            return note

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
    ) -> Optional[Note]:
        """Updates an existing Note entity with atomic transaction."""
        now = datetime.now().isoformat()
        temp_note = Note(title=title, content=content)
        tags = ",".join(sorted(temp_note.extract_hashtags()))

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE notes
                SET title = ?, content = ?, content_html = ?, theme = ?, pinned = ?, is_locked = ?, tags = ?, background_style = ?, updated_at = ?
                WHERE id = ?;
                """,
                (
                    title,
                    content,
                    content_html,
                    theme,
                    1 if pinned else 0,
                    1 if is_locked else 0,
                    tags,
                    background_style,
                    now,
                    note_id,
                ),
            )
            conn.commit()
            if cursor.rowcount > 0:
                return self.get_note_by_id(note_id)
            return None

    def toggle_pin(self, note_id: int) -> Optional[Note]:
        """Toggles the pinned status of a note."""
        note = self.get_note_by_id(note_id)
        if note and note.id:
            return self.update_note(
                note_id=note.id,
                title=note.title,
                content=note.content,
                content_html=note.content_html,
                theme=note.theme,
                pinned=not note.pinned,
                is_locked=note.is_locked,
                background_style=note.background_style,
            )
        return None

    def toggle_lock(self, note_id: int) -> Optional[Note]:
        """Toggles the is_locked status of a note."""
        note = self.get_note_by_id(note_id)
        if note and note.id:
            return self.update_note(
                note_id=note.id,
                title=note.title,
                content=note.content,
                content_html=note.content_html,
                theme=note.theme,
                pinned=note.pinned,
                is_locked=not note.is_locked,
                background_style=note.background_style,
            )
        return None

    def delete_note(self, note_id: int) -> bool:
        """Deletes a Note entity by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM notes WHERE id = ?;", (note_id,))
            conn.commit()
            return cursor.rowcount > 0
