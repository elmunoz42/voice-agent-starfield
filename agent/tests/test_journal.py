"""
Unit tests for journal module
"""

import pytest
import tempfile
from pathlib import Path
from journal import JournalDB, SPOILER_LEVELS


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    journal = JournalDB(db_path)
    yield journal

    # Cleanup
    db_path.unlink(missing_ok=True)


def test_log_progress(temp_db):
    """Test logging progress entries."""
    entry_id = temp_db.log_progress("Completed first mission")
    assert entry_id > 0

    # Log with topic
    entry_id2 = temp_db.log_progress("Found a Class B ship", topic="ships")
    assert entry_id2 > entry_id


def test_recall_progress(temp_db):
    """Test recalling progress entries."""
    # Log some entries
    temp_db.log_progress("Entry 1", topic="combat")
    temp_db.log_progress("Entry 2", topic="exploration")
    temp_db.log_progress("Entry 3", topic="combat")

    # Recall all
    all_entries = temp_db.recall_progress()
    assert len(all_entries) == 3

    # Recall by topic
    combat_entries = temp_db.recall_progress(topic="combat")
    assert len(combat_entries) == 2


def test_get_recent_progress(temp_db):
    """Test getting recent progress for session context."""
    for i in range(5):
        temp_db.log_progress(f"Entry {i}")

    recent = temp_db.get_recent_progress(limit=3)
    assert len(recent) == 3
    # Should be in reverse chronological order
    assert recent[0]["note"] == "Entry 4"


def test_set_get_current_goal(temp_db):
    """Test goal management."""
    # No goal initially
    assert temp_db.get_current_goal() is None

    # Set a goal
    temp_db.set_current_goal("Find a better ship")
    assert temp_db.get_current_goal() == "Find a better ship"

    # Update goal (old one should no longer be current)
    temp_db.set_current_goal("Build an outpost")
    assert temp_db.get_current_goal() == "Build an outpost"


def test_spoiler_level(temp_db):
    """Test spoiler level management."""
    # Default is 'none'
    assert temp_db.get_spoiler_level() == "none"

    # Set to main-quest
    temp_db.set_spoiler_level("main-quest")
    assert temp_db.get_spoiler_level() == "main-quest"

    # Invalid level raises ValueError
    with pytest.raises(ValueError):
        temp_db.set_spoiler_level("invalid")


def test_get_allowed_spoiler_levels(temp_db):
    """Test spoiler level filtering."""
    # Default 'none'
    assert temp_db.get_allowed_spoiler_levels() == ["none"]

    # Set to faction
    temp_db.set_spoiler_level("faction")
    allowed = temp_db.get_allowed_spoiler_levels()
    assert allowed == ["none", "main-quest", "faction"]
    assert "endgame" not in allowed


def test_session_context(temp_db):
    """Test getting session context."""
    # Empty journal
    context = temp_db.get_session_context()
    assert context["current_goal"] is None
    assert context["recent_progress"] == []
    assert context["spoiler_level"] == "none"

    # Add some data
    temp_db.log_progress("Did something")
    temp_db.set_current_goal("Do something else")
    temp_db.set_spoiler_level("main-quest")

    context = temp_db.get_session_context()
    assert context["current_goal"] == "Do something else"
    assert len(context["recent_progress"]) == 1
    assert context["spoiler_level"] == "main-quest"


def test_idempotent_schema_init(temp_db):
    """Test that re-initializing schema doesn't break."""
    temp_db.log_progress("Test entry")
    temp_db._init_schema()  # Should not raise or clear data
    entries = temp_db.recall_progress()
    assert len(entries) == 1
