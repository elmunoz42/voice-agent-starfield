"""
Progress Journal Module for AstroLB-3
======================================
SQLite-based progress tracking, goals, and spoiler level management.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

# Spoiler level hierarchy
SPOILER_LEVELS = ["none", "main-quest", "faction", "endgame"]


def _resolve_data_dir() -> Path:
    """Locate the data directory (journal + knowledge base).

    $ASTRO_DATA_DIR if set (the cloud image sets /app/data, since ../data is
    outside the build context and not writable), else ../data for local dev.
    """
    if os.getenv("ASTRO_DATA_DIR"):
        return Path(os.environ["ASTRO_DATA_DIR"])
    return Path(__file__).parent / "../data"


DATA_DIR = _resolve_data_dir()

# Default database path
DEFAULT_DB_PATH = DATA_DIR / "journal.db"


class JournalDB:
    """SQLite-based progress journal for AstroLB-3."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize journal database.

        Args:
            db_path: Path to SQLite database file. Defaults to data/journal.db
        """
        self.db_path = db_path or DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        """Initialize database schema if not exists."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Progress entries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    note TEXT NOT NULL,
                    topic TEXT
                )
            """)

            # Goals table (only current goal matters)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    is_current BOOLEAN NOT NULL DEFAULT 1
                )
            """)

            # Settings table (key-value store)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)

            conn.commit()

        logger.info(f"Journal database initialized at {self.db_path}")

    # Progress tracking

    def log_progress(self, note: str, topic: Optional[str] = None) -> int:
        """Log a progress entry.

        Args:
            note: Progress note text
            topic: Optional topic/category for the entry

        Returns:
            ID of the created entry
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            cursor.execute(
                "INSERT INTO progress (timestamp, note, topic) VALUES (?, ?, ?)",
                (timestamp, note, topic)
            )
            conn.commit()

            entry_id = cursor.lastrowid
            logger.info(f"Logged progress entry {entry_id}: {note[:50]}...")

            return entry_id

    def recall_progress(
        self, topic: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recall recent progress entries, optionally filtered by topic.

        Args:
            topic: Optional topic to filter by
            limit: Maximum number of entries to return

        Returns:
            List of progress entries (newest first)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if topic:
                cursor.execute(
                    """
                    SELECT id, timestamp, note, topic
                    FROM progress
                    WHERE topic LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"%{topic}%", limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, timestamp, note, topic
                    FROM progress
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,)
                )

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_progress(self, limit: int = 3) -> List[Dict[str, Any]]:
        """Get most recent progress entries for session context.

        Args:
            limit: Number of recent entries (default 3)

        Returns:
            List of recent progress entries (newest first)
        """
        return self.recall_progress(limit=limit)

    # Goal management

    def set_current_goal(self, goal: str) -> int:
        """Set the current goal, marking all others as not current.

        Args:
            goal: The new current goal text

        Returns:
            ID of the new goal entry
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            # Mark all existing goals as not current
            cursor.execute("UPDATE goals SET is_current = 0")

            # Insert new current goal
            cursor.execute(
                "INSERT INTO goals (timestamp, goal, is_current) VALUES (?, ?, 1)",
                (timestamp, goal)
            )
            conn.commit()

            goal_id = cursor.lastrowid
            logger.info(f"Set current goal: {goal}")

            return goal_id

    def get_current_goal(self) -> Optional[str]:
        """Get the current goal.

        Returns:
            Current goal text, or None if no goal is set
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT goal FROM goals WHERE is_current = 1 ORDER BY timestamp DESC LIMIT 1"
            )
            row = cursor.fetchone()

            return row["goal"] if row else None

    # Spoiler level management

    def set_spoiler_level(self, level: str) -> None:
        """Set the spoiler level.

        Args:
            level: Spoiler level (none, main-quest, faction, endgame)

        Raises:
            ValueError: If level is invalid
        """
        if level not in SPOILER_LEVELS:
            raise ValueError(
                f"Invalid spoiler level '{level}'. Must be one of: {', '.join(SPOILER_LEVELS)}"
            )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES ('spoiler_level', ?, ?)
                """,
                (level, timestamp)
            )
            conn.commit()

            logger.info(f"Set spoiler level to: {level}")

    def get_spoiler_level(self) -> str:
        """Get the current spoiler level.

        Returns:
            Current spoiler level (defaults to 'none')
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM settings WHERE key = 'spoiler_level'"
            )
            row = cursor.fetchone()

            return row["value"] if row else "none"

    def get_allowed_spoiler_levels(self) -> List[str]:
        """Get list of allowed spoiler levels based on current setting.

        Returns:
            List of allowed levels (e.g., if current is 'faction', returns ['none', 'main-quest', 'faction'])
        """
        current_level = self.get_spoiler_level()
        try:
            index = SPOILER_LEVELS.index(current_level)
            return SPOILER_LEVELS[:index + 1]
        except ValueError:
            # Default to none if invalid
            return ["none"]

    # Session context

    def get_session_context(self) -> Dict[str, Any]:
        """Get context for session greeting.

        Returns:
            Dictionary with current_goal, recent_progress, and spoiler_level
        """
        return {
            "current_goal": self.get_current_goal(),
            "recent_progress": self.get_recent_progress(limit=3),
            "spoiler_level": self.get_spoiler_level()
        }


# Singleton instance for easy access
_journal_instance: Optional[JournalDB] = None


def get_journal(db_path: Optional[Path] = None) -> JournalDB:
    """Get the global journal instance (singleton).

    Args:
        db_path: Optional database path (only used on first call)

    Returns:
        JournalDB instance
    """
    global _journal_instance

    if _journal_instance is None:
        _journal_instance = JournalDB(db_path)

    return _journal_instance
