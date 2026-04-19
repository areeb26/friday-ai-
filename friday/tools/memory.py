"""
Memory tools — notes, timers, reminders with SQLite persistence.
"""

import sqlite3
import os
import logging
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

logger = logging.getLogger("friday.tools.memory")

# Database path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "friday_memory.db"

# Global timer storage (in-memory for active timers)
_active_timers: Dict[str, dict] = {}


def _init_db():
    """Initialize database tables if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Notes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tag TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Reminders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            remind_at TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("Memory database initialized")


# Auto-init on module load
_init_db()


def register(mcp):

    @mcp.tool()
    def save_note(content: str, tag: str = "general") -> str:
        """Save a note with optional category tag."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO notes (content, tag) VALUES (?, ?)",
                (content, tag)
            )
            conn.commit()
            note_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"Note saved: id={note_id}, tag={tag}")
            return f"Noted and filed under '{tag}', boss. (ID: {note_id})"
            
        except Exception as e:
            logger.error(f"Save note failed: {e}")
            return "My memory banks are having trouble, boss. Trying again..."

    @mcp.tool()
    def get_notes(tag: str = None) -> list:
        """Retrieve notes. If tag provided, filter by category."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if tag:
                cursor.execute(
                    "SELECT id, content, tag, created_at FROM notes WHERE tag = ? ORDER BY created_at DESC",
                    (tag,)
                )
            else:
                cursor.execute(
                    "SELECT id, content, tag, created_at FROM notes ORDER BY created_at DESC LIMIT 20"
                )
            
            rows = cursor.fetchall()
            conn.close()
            
            notes = [dict(row) for row in rows]
            logger.info(f"Retrieved {len(notes)} notes")
            return notes
            
        except Exception as e:
            logger.error(f"Get notes failed: {e}")
            return []

    @mcp.tool()
    async def set_timer(minutes: int, label: str = "Timer") -> str:
        """Set a countdown timer. FRIDAY will alert you when done."""
        try:
            # Check max timers
            if len(_active_timers) >= 5:
                return "I've got 5 timers running already, boss. Clear one first?"
            
            timer_id = f"timer_{len(_active_timers)}_{datetime.now().strftime('%H%M%S')}"
            end_time = datetime.now() + timedelta(minutes=minutes)
            
            _active_timers[timer_id] = {
                "label": label,
                "end_time": end_time,
                "active": True
            }
            
            # Start background task
            asyncio.create_task(_timer_task(timer_id, minutes, label))
            
            logger.info(f"Timer set: {label} for {minutes} minutes")
            return f"Timer set for {minutes} minutes. Standing by, boss. ({label})"
            
        except Exception as e:
            logger.error(f"Set timer failed: {e}")
            return "Can't set that timer, boss. Try again?"

    @mcp.tool()
    def set_reminder(time: str, message: str) -> str:
        """Set a reminder for a specific time (e.g., '3pm', '15:30', 'in 30 minutes')."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Parse time (simple implementation)
            now = datetime.now()
            remind_at = None
            
            time_lower = time.lower().strip()
            
            if time_lower.startswith("in "):
                # Handle "in 30 minutes" or "in 1 hour"
                parts = time_lower.replace("in ", "").split()
                if len(parts) >= 2:
                    try:
                        amount = int(parts[0])
                        unit = parts[1]
                        if "minute" in unit:
                            remind_at = now + timedelta(minutes=amount)
                        elif "hour" in unit:
                            remind_at = now + timedelta(hours=amount)
                    except ValueError:
                        pass
            elif time_lower == "now":
                remind_at = now
            else:
                # Try to parse as HH:MM or H:MM AM/PM
                try:
                    # Try 24-hour format first
                    remind_at = datetime.strptime(time, "%H:%M")
                    remind_at = remind_at.replace(year=now.year, month=now.month, day=now.day)
                    if remind_at < now:
                        remind_at += timedelta(days=1)  # Tomorrow
                except ValueError:
                    # Try 12-hour format
                    try:
                        remind_at = datetime.strptime(time, "%I:%M %p")
                        remind_at = remind_at.replace(year=now.year, month=now.month, day=now.day)
                        if remind_at < now:
                            remind_at += timedelta(days=1)
                    except ValueError:
                        pass
            
            if remind_at is None:
                return f"I didn't understand that time format, boss. Try '3pm', '15:30', or 'in 30 minutes'."
            
            cursor.execute(
                "INSERT INTO reminders (message, remind_at) VALUES (?, ?)",
                (message, remind_at.isoformat())
            )
            conn.commit()
            conn.close()
            
            time_str = remind_at.strftime("%I:%M %p")
            return f"Reminder set for {time_str}, boss. I'll ping you: '{message}'"
            
        except Exception as e:
            logger.error(f"Set reminder failed: {e}")
            return "Can't set that reminder, boss. Try a different time format?"


async def _timer_task(timer_id: str, minutes: int, label: str):
    """Background task for timer countdown."""
    await asyncio.sleep(minutes * 60)
    
    if timer_id in _active_timers and _active_timers[timer_id]["active"]:
        logger.info(f"Timer complete: {label}")
        # Mark as complete
        _active_timers[timer_id]["active"] = False
        # The actual alert would be spoken by FRIDAY's voice system
        # For now, we just log it
        logger.info(f"ALERT: Timer '{label}' is complete!")
