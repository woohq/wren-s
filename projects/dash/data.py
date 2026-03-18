"""Data storage layer for a personal dashboard app.

All data lives under ~/.dash/. Each store manages its own JSON file(s)
and creates directories automatically on first use.

Classes:
    TaskStore  — tasks in ~/.dash/tasks.json
    HabitStore — habits in ~/.dash/habits.json
    NoteStore  — notes as individual JSON files in ~/.dash/notes/
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any


_DASH_DIR = Path.home() / ".dash"


def _ensure_dir(path: Path) -> None:
    """Create a directory (and parents) if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def _read_json(path: Path) -> Any:
    """Read JSON from *path*, returning an empty list on missing/corrupt files."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def _write_json(path: Path, data: Any) -> None:
    """Atomically-ish write *data* as JSON to *path*."""
    _ensure_dir(path.parent)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _short_id() -> str:
    """Return a 6-character random hex string."""
    return secrets.token_hex(3)


# ---------------------------------------------------------------------------
# TaskStore
# ---------------------------------------------------------------------------

class TaskStore:
    """Manage tasks stored in ``~/.dash/tasks.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DASH_DIR / "tasks.json"

    # -- persistence helpers ------------------------------------------------

    def _load(self) -> list[dict]:
        data = _read_json(self._path)
        return data if isinstance(data, list) else []

    def _save(self, tasks: list[dict]) -> None:
        _write_json(self._path, tasks)

    # -- public API ---------------------------------------------------------

    def add(self, text: str, priority: str = "normal") -> dict:
        """Add a task and return it."""
        task: dict = {
            "id": _short_id(),
            "text": text,
            "priority": priority,
            "created_at": datetime.now().isoformat(),
            "done": False,
        }
        tasks = self._load()
        tasks.append(task)
        self._save(tasks)
        return task

    def complete(self, task_id: str) -> None:
        """Mark a task as done."""
        tasks = self._load()
        for t in tasks:
            if t["id"] == task_id:
                t["done"] = True
                break
        self._save(tasks)

    def remove(self, task_id: str) -> None:
        """Delete a task by id."""
        tasks = [t for t in self._load() if t["id"] != task_id]
        self._save(tasks)

    def list_tasks(self, show_done: bool = False) -> list[dict]:
        """Return tasks.  Excludes completed tasks unless *show_done* is True."""
        tasks = self._load()
        if not show_done:
            tasks = [t for t in tasks if not t.get("done")]
        return tasks

    def clear_done(self) -> None:
        """Remove all completed tasks."""
        tasks = [t for t in self._load() if not t.get("done")]
        self._save(tasks)


# ---------------------------------------------------------------------------
# HabitStore
# ---------------------------------------------------------------------------

class HabitStore:
    """Manage habits stored in ``~/.dash/habits.json``."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DASH_DIR / "habits.json"

    # -- persistence helpers ------------------------------------------------

    def _load(self) -> list[dict]:
        data = _read_json(self._path)
        return data if isinstance(data, list) else []

    def _save(self, habits: list[dict]) -> None:
        _write_json(self._path, habits)

    def _find(self, name: str, habits: list[dict]) -> dict | None:
        for h in habits:
            if h["name"] == name:
                return h
        return None

    # -- public API ---------------------------------------------------------

    def add(self, name: str) -> dict:
        """Create a new habit to track."""
        habits = self._load()
        if self._find(name, habits) is not None:
            raise ValueError(f"Habit already exists: {name!r}")
        habit: dict = {
            "name": name,
            "created_at": datetime.now().isoformat(),
            "checks": [],
        }
        habits.append(habit)
        self._save(habits)
        return habit

    def check(self, name: str) -> None:
        """Mark a habit as done for today."""
        habits = self._load()
        habit = self._find(name, habits)
        if habit is None:
            raise KeyError(f"Habit not found: {name!r}")
        today = date.today().isoformat()
        if today not in habit["checks"]:
            habit["checks"].append(today)
        self._save(habits)

    def uncheck(self, name: str) -> None:
        """Remove today's check from a habit."""
        habits = self._load()
        habit = self._find(name, habits)
        if habit is None:
            raise KeyError(f"Habit not found: {name!r}")
        today = date.today().isoformat()
        if today in habit["checks"]:
            habit["checks"].remove(today)
        self._save(habits)

    def remove(self, name: str) -> None:
        """Delete a habit entirely."""
        habits = [h for h in self._load() if h["name"] != name]
        self._save(habits)

    def list_habits(self) -> list[dict]:
        """Return all habits with their check history."""
        return self._load()

    def streak(self, name: str) -> int:
        """Calculate the current streak of consecutive days (including today).

        Returns 0 if today is not checked.
        """
        habits = self._load()
        habit = self._find(name, habits)
        if habit is None:
            raise KeyError(f"Habit not found: {name!r}")

        checks = sorted(set(habit["checks"]), reverse=True)
        if not checks:
            return 0

        today = date.today().isoformat()
        if checks[0] != today:
            return 0

        count = 1
        for i in range(1, len(checks)):
            expected = (date.today() - timedelta(days=i)).isoformat()
            if checks[i] == expected:
                count += 1
            else:
                break
        return count


# ---------------------------------------------------------------------------
# NoteStore
# ---------------------------------------------------------------------------

class NoteStore:
    """Manage quick notes as individual JSON files in ``~/.dash/notes/``."""

    def __init__(self, directory: Path | None = None) -> None:
        self._dir = directory or _DASH_DIR / "notes"
        _ensure_dir(self._dir)

    # -- persistence helpers ------------------------------------------------

    def _note_path(self, note_id: str) -> Path:
        return self._dir / f"{note_id}.json"

    def _load_note(self, path: Path) -> dict | None:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def _all_notes(self) -> list[dict]:
        notes: list[dict] = []
        for p in self._dir.glob("*.json"):
            note = self._load_note(p)
            if note is not None:
                notes.append(note)
        return notes

    # -- public API ---------------------------------------------------------

    def add(self, text: str, tags: list[str] | None = None) -> dict:
        """Save a note and return it."""
        if tags is None:
            tags = []
        note_id = _short_id()
        note: dict = {
            "id": note_id,
            "text": text,
            "tags": list(tags),
            "created_at": datetime.now().isoformat(),
        }
        path = self._note_path(note_id)
        _write_json(path, note)
        return note

    def search(self, query: str) -> list[dict]:
        """Search notes by text content (case-insensitive substring match)."""
        q = query.lower()
        return [n for n in self._all_notes() if q in n.get("text", "").lower()]

    def recent(self, n: int = 5) -> list[dict]:
        """Return the most recent *n* notes."""
        notes = self._all_notes()
        notes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return notes[:n]

    def list_tags(self) -> dict[str, int]:
        """Return a mapping of tag -> count across all notes."""
        counts: dict[str, int] = {}
        for note in self._all_notes():
            for tag in note.get("tags", []):
                counts[tag] = counts.get(tag, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# ReflectStore
# ---------------------------------------------------------------------------

class ReflectStore:
    """Track daily reflections — mood scores, accomplishments, gratitude.

    Stored in ``~/.dash/reflections.json`` as a list of daily entries.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or _DASH_DIR / "reflections.json"

    def _load(self) -> list[dict]:
        data = _read_json(self._path)
        return data if isinstance(data, list) else []

    def _save(self, data: list[dict]) -> None:
        _write_json(self._path, data)

    def add(self, score: int, note: str = "", grateful: str = "") -> dict:
        """Add today's reflection. Overwrites if already reflected today."""
        entries = self._load()
        today = date.today().isoformat()

        entry = {
            "date": today,
            "score": max(1, min(10, score)),
            "note": note,
            "grateful": grateful,
            "created_at": datetime.now().isoformat(),
        }

        # Replace existing entry for today, or append
        entries = [e for e in entries if e.get("date") != today]
        entries.append(entry)
        entries.sort(key=lambda x: x.get("date", ""))
        self._save(entries)
        return entry

    def today(self) -> dict | None:
        """Get today's reflection, if it exists."""
        today = date.today().isoformat()
        for entry in self._load():
            if entry.get("date") == today:
                return entry
        return None

    def recent(self, n: int = 7) -> list[dict]:
        """Get the last N reflections."""
        entries = self._load()
        entries.sort(key=lambda x: x.get("date", ""), reverse=True)
        return entries[:n]

    def streak(self) -> int:
        """How many consecutive days you've reflected (including today)."""
        entries = self._load()
        dates = sorted(set(e.get("date", "") for e in entries), reverse=True)
        if not dates:
            return 0
        today = date.today().isoformat()
        if dates[0] != today:
            return 0
        count = 1
        for i in range(1, len(dates)):
            expected = (date.today() - timedelta(days=i)).isoformat()
            if dates[i] == expected:
                count += 1
            else:
                break
        return count

    def average_score(self, days: int = 7) -> float | None:
        """Average mood score over the last N days."""
        recent = self.recent(days)
        if not recent:
            return None
        scores = [e["score"] for e in recent if "score" in e]
        return sum(scores) / len(scores) if scores else None

    def mood_sparkline(self, days: int = 14) -> str:
        """Render mood scores as a sparkline."""
        entries = {e["date"]: e["score"] for e in self._load()}
        today = date.today()
        chars = "▁▂▃▄▅▆▇█"
        spark = []
        for i in range(days - 1, -1, -1):
            day = (today - timedelta(days=i)).isoformat()
            score = entries.get(day)
            if score is not None:
                idx = min(len(chars) - 1, int((score - 1) / 9 * (len(chars) - 1)))
                spark.append(chars[idx])
            else:
                spark.append(" ")
        return ''.join(spark)
