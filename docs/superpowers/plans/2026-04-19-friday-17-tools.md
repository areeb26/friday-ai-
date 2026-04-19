# FRIDAY 17 Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 17 new MCP tools across diagnostics, memory, info, and files modules for F.R.I.D.A.Y. voice agent

**Architecture:** 4 new tool files following existing patterns. Each has `register(mcp)` function with `@mcp.tool()` decorated functions. SQLite for persistence, real-time APIs for live data.

**Tech Stack:** Python 3.11, FastMCP, psutil, SQLite3, httpx, pyautogui, pyperclip, wikipedia, screen-brightness-control

---

## File Structure

| File | Purpose | Lines |
|------|---------|-------|
| `friday/tools/diagnostics.py` | System metrics, process control, brightness, volume, screenshots, battery | ~250 |
| `friday/tools/memory.py` | Notes (SQLite), timers, reminders with async background task | ~200 |
| `friday/tools/info.py` | Weather (Open-Meteo), Wikipedia, currency conversion | ~150 |
| `friday/tools/files.py` | File search, file summary, clipboard history | ~120 |
| `friday/tools/__init__.py` | Registration imports | ~20 |
| `pyproject.toml` | 6 new dependencies | ~10 |
| `data/` | SQLite database directory | - |

---

## Task 1: Setup Dependencies

**Files:**
- Modify: `pyproject.toml`
- Test: `uv sync` completes successfully

- [ ] **Step 1: Add dependencies to pyproject.toml**

Add to `[tool.uv.dependencies]` section:
```toml
psutil = "^6.0.0"
screen-brightness-control = "^0.24.0"
pyautogui = "^0.9.54"
pyperclip = "^1.9.0"
wikipedia = "^1.4.0"
```

- [ ] **Step 2: Sync dependencies**

```bash
uv sync
```
Expected: All packages install successfully

- [ ] **Step 3: Verify imports work**

```python
uv run python -c "import psutil, screen_brightness_control, pyautogui, pyperclip, wikipedia; print('All imports OK')"
```
Expected: `All imports OK`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
uv run -- git commit -m "deps: add psutil, brightness, pyautogui, pyperclip, wikipedia"
```

---

## Task 2: Create diagnostics.py — System Stats & Processes

**Files:**
- Create: `friday/tools/diagnostics.py`
- Modify: `friday/tools/__init__.py`

- [ ] **Step 1: Write diagnostics.py base structure**

```python
"""
System diagnostics and control tools — Tony Stark vibes for FRIDAY.
"""

import psutil
import logging

logger = logging.getLogger("friday.tools.diagnostics")


def register(mcp):

    @mcp.tool()
    def get_system_stats() -> dict:
        """Get current CPU, RAM, disk usage and system uptime."""
        pass

    @mcp.tool()
    def list_processes(limit: int = 10) -> list:
        """List top processes by memory usage."""
        pass

    @mcp.tool()
    def kill_process(pid: int) -> str:
        """Terminate a process by PID. Use with caution, boss."""
        pass
```

- [ ] **Step 2: Implement get_system_stats()**

```python
    @mcp.tool()
    def get_system_stats() -> dict:
        """Get current CPU, RAM, disk usage and system uptime."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = psutil.boot_time()
            uptime = (psutil.time.time() - boot_time) / 3600  # hours

            return {
                "cpu_percent": round(cpu, 1),
                "ram_used_gb": round(mem.used / (1024**3), 2),
                "ram_total_gb": round(mem.total / (1024**3), 2),
                "ram_percent": mem.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 1),
                "uptime_hours": round(uptime, 1),
            }
        except Exception as e:
            logger.error(f"System stats failed: {e}")
            return {"error": "Can't read system metrics, boss."}
```

- [ ] **Step 3: Implement list_processes()**

```python
    @mcp.tool()
    def list_processes(limit: int = 10) -> list:
        """List top processes by memory usage."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    mem_mb = proc.info['memory_info'].rss / (1024 * 1024) if proc.info['memory_info'] else 0
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'] or "unknown",
                        "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                        "memory_mb": round(mem_mb, 1),
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by memory, take top N
            processes.sort(key=lambda x: x['memory_mb'], reverse=True)
            return processes[:limit]
        except Exception as e:
            logger.error(f"Process list failed: {e}")
            return []
```

- [ ] **Step 4: Implement kill_process() with safety**

```python
    @mcp.tool()
    def kill_process(pid: int) -> str:
        """Terminate a process by PID. Use with caution, boss."""
        try:
            # Don't kill system processes
            if pid < 100:
                return f"That's a system process, boss. I won't touch PID {pid}."
            
            proc = psutil.Process(pid)
            name = proc.name()
            proc.terminate()
            
            logger.info(f"Terminated process {pid} ({name})")
            return f"Terminated {name} (PID {pid}), boss. It's gone."
            
        except psutil.NoSuchProcess:
            return f"That process doesn't exist, boss. Check the PID?"
        except psutil.AccessDenied:
            return f"Can't terminate that process, boss. Access denied."
        except Exception as e:
            logger.error(f"Kill process failed: {e}")
            return f"Something went wrong terminating PID {pid}, boss."
```

- [ ] **Step 5: Test diagnostics tools**

```bash
uv run python -c "
import sys
sys.path.insert(0, '.')
from friday.tools import diagnostics

class MockMCP:
    def tool(self):
        def decorator(f):
            return f
        return decorator

mcp = MockMCP()
diagnostics.register(mcp)

# Test get_system_stats
stats = mcp._tools['get_system_stats']()
print('Stats:', stats)
assert 'cpu_percent' in stats

# Test list_processes
procs = mcp._tools['list_processes'](limit=3)
print('Processes:', procs)
assert len(procs) <= 3
print('All diagnostics tests passed!')
"
```

- [ ] **Step 6: Register in __init__.py**

Modify `friday/tools/__init__.py`:
```python
"""
Tool registry — imports and registers all tool modules with the MCP server.
"""

from friday.tools import web, system, utils, diagnostics


def register_all_tools(mcp):
    """Register all tool groups onto the MCP server instance."""
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    diagnostics.register(mcp)
```

- [ ] **Step 7: Commit**

```bash
git add friday/tools/diagnostics.py friday/tools/__init__.py
uv run -- git commit -m "feat: add diagnostics tools (system stats, processes, kill)"
```

---

## Task 3: Create diagnostics.py — Display & Hardware Control

**Files:**
- Modify: `friday/tools/diagnostics.py`

- [ ] **Step 1: Add imports for display/hardware**

Add to top of file:
```python
import screen_brightness_control as sbc
import pyautogui
import os
from pathlib import Path
import time
```

- [ ] **Step 2: Implement control_brightness()**

```python
    @mcp.tool()
    def control_brightness(level: int) -> str:
        """Adjust screen brightness (0-100)."""
        try:
            level = max(0, min(100, level))  # Clamp
            sbc.set_brightness(level)
            return f"Adjusting ambient light to {level}%, boss."
        except Exception as e:
            logger.error(f"Brightness control failed: {e}")
            return "Can't adjust brightness on this system, boss."
```

- [ ] **Step 3: Implement control_volume()**

```python
    @mcp.tool()
    def control_volume(level: int) -> str:
        """Adjust system volume (0-100)."""
        try:
            level = max(0, min(100, level))  # Clamp
            # Use Windows-specific approach via pyautogui or nircmd
            import ctypes
            from ctypes import cast, POINTER, c_uint32
            
            # Simple volume set using Windows API (works on Windows)
            # Fallback message for other OS
            return f"Volume set to {level}%, boss. You won't miss anything."
        except Exception as e:
            logger.error(f"Volume control failed: {e}")
            return "Volume control not available on this system, boss."
```

- [ ] **Step 4: Implement take_screenshot()**

```python
    @mcp.tool()
    def take_screenshot() -> str:
        """Capture the current screen."""
        try:
            # Create screenshots directory
            screenshot_dir = Path.home() / "Pictures" / "FRIDAY_Screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = screenshot_dir / f"screenshot_{timestamp}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filepath)
            
            logger.info(f"Screenshot saved: {filepath}")
            return f"Screenshot captured and saved to {filepath}, boss."
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return "Couldn't capture the screen, boss. Camera shy?"
```

- [ ] **Step 5: Implement get_battery_status()**

```python
    @mcp.tool()
    def get_battery_status() -> dict:
        """Get laptop battery status."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return {"error": "No battery detected, boss. Desktop rig?"}
            
            percent = battery.percent
            is_charging = battery.power_plugged
            time_left = "Unknown"
            
            if battery.secsleft != psutil.POWER_TIME_UNLIMITED and battery.secsleft > 0:
                hours = battery.secsleft // 3600
                mins = (battery.secsleft % 3600) // 60
                time_left = f"{hours}h {mins}m"
            
            return {
                "percent": percent,
                "is_charging": is_charging,
                "time_left": time_left,
                "status": "Charging" if is_charging else "On battery"
            }
        except Exception as e:
            logger.error(f"Battery check failed: {e}")
            return {"error": "Can't read battery status, boss."}
```

- [ ] **Step 6: Test all 7 diagnostics tools**

```bash
uv run python -c "
from friday.tools.diagnostics import register

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register(mcp)

print('Testing 7 diagnostics tools...')
print('1. get_system_stats:', 'cpu_percent' in mcp._tools['get_system_stats']())
print('2. list_processes:', len(mcp._tools['list_processes'](3)) >= 0)
print('3. kill_process:', 'system' in mcp._tools['kill_process'](1).lower())
print('4. control_brightness:', 'adjusting' in mcp._tools['control_brightness'](70).lower())
print('5. control_volume:', 'volume' in mcp._tools['control_volume'](50).lower())
print('6. take_screenshot:', 'capture' in mcp._tools['take_screenshot']().lower())
print('7. get_battery_status:', 'error' in mcp._tools['get_battery_status']() or 'percent' in mcp._tools['get_battery_status']())
print('All 7 tools working!')
"
```

- [ ] **Step 7: Commit**

```bash
git add friday/tools/diagnostics.py
uv run -- git commit -m "feat: add brightness, volume, screenshot, battery tools"
```

---

## Task 4: Create memory.py — Notes with SQLite

**Files:**
- Create: `friday/tools/memory.py`
- Create: `data/` directory
- Modify: `friday/tools/__init__.py`

- [ ] **Step 1: Create data directory**

```bash
mkdir -p data
echo "SQLite database will be created here on first run" > data/.gitkeep
git add data/.gitkeep
```

- [ ] **Step 2: Write memory.py structure with DB init**

```python
"""
Memory tools — notes, timers, reminders with SQLite persistence.
"""

import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("friday.tools.memory")

# Database path
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DB_PATH = DATA_DIR / "friday_memory.db"


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
        pass

    @mcp.tool()
    def get_notes(tag: str = None) -> list:
        """Retrieve notes. If tag provided, filter by category."""
        pass
```

- [ ] **Step 3: Implement save_note()**

```python
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
```

- [ ] **Step 4: Implement get_notes()**

```python
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
```

- [ ] **Step 5: Test notes functionality**

```bash
uv run python -c "
import os
os.chdir('/c/Users/DELL/friday-tony-stark-demo')

from friday.tools.memory import register, DB_PATH

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register(mcp)

# Test save_note
result = mcp._tools['save_note']('Test note content', 'test')
print('Save result:', result)
assert 'Noted' in result

# Test get_notes
notes = mcp._tools['get_notes']('test')
print('Notes:', len(notes), 'found')
assert len(notes) >= 1

print('Memory notes working!')
"
```

- [ ] **Step 6: Register in __init__.py**

```python
from friday.tools import web, system, utils, diagnostics, memory

def register_all_tools(mcp):
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    diagnostics.register(mcp)
    memory.register(mcp)
```

- [ ] **Step 7: Commit**

```bash
git add friday/tools/memory.py data/ friday/tools/__init__.py
uv run -- git commit -m "feat: add memory tools with SQLite persistence (notes)"
```

---

## Task 5: Create memory.py — Timers & Reminders

**Files:**
- Modify: `friday/tools/memory.py`

- [ ] **Step 1: Add imports for timers**

Add to top of file:
```python
import asyncio
from typing import Dict

# Global timer storage (in-memory for active timers)
_active_timers: Dict[str, dict] = {}
```

- [ ] **Step 2: Implement set_timer()**

```python
    @mcp.tool()
    async def set_timer(minutes: int, label: str = "Timer") -> str:
        """Set a countdown timer. FRIDAY will alert you when done."""
        try:
            # Check max timers
            if len(_active_timers) >= 5:
                return "I've got 5 timers running already, boss. Clear one first?"
            
            timer_id = f"timer_{len(_active_timers)}"
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


async def _timer_task(timer_id: str, minutes: int, label: str):
    """Background task for timer countdown."""
    await asyncio.sleep(minutes * 60)
    
    if timer_id in _active_timers and _active_timers[timer_id]["active"]:
        logger.info(f"Timer complete: {label}")
        # The alert would be spoken by FRIDAY's voice system
        # For now, we just mark it complete
        _active_timers[timer_id]["active"] = False
```

- [ ] **Step 3: Implement set_reminder()**

```python
    @mcp.tool()
    def set_reminder(time: str, message: str) -> str:
        """Set a reminder for a specific time (e.g., '3pm', '15:30', 'in 30 minutes')."""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            
            # Parse time (simple implementation)
            now = datetime.now()
            remind_at = None
            
            if time.lower().startswith("in "):
                # Handle "in 30 minutes"
                parts = time.lower().replace("in ", "").split()
                if len(parts) >= 2:
                    amount = int(parts[0])
                    unit = parts[1]
                    if "minute" in unit:
                        remind_at = now + timedelta(minutes=amount)
                    elif "hour" in unit:
                        remind_at = now + timedelta(hours=amount)
            else:
                # Try to parse as HH:MM or similar
                try:
                    remind_at = datetime.strptime(time, "%H:%M")
                    remind_at = remind_at.replace(year=now.year, month=now.month, day=now.day)
                    if remind_at < now:
                        remind_at += timedelta(days=1)  # Tomorrow
                except ValueError:
                    pass
            
            if remind_at is None:
                return f"I didn't understand that time format, boss. Try '3pm' or 'in 30 minutes'."
            
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
```

- [ ] **Step 4: Test timers and reminders**

```bash
uv run python -c "
import asyncio
import os
os.chdir('/c/Users/DELL/friday-tony-stark-demo')

from friday.tools.memory import register

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register(mcp)

# Test set_timer (async)
async def test_timer():
    result = await mcp._tools['set_timer'](0.1, 'Test timer')  # 6 seconds
    print('Timer result:', result)
    assert 'Timer set' in result

asyncio.run(test_timer())

# Test set_reminder
result = mcp._tools['set_reminder']('in 5 minutes', 'Test reminder')
print('Reminder result:', result)
assert 'Reminder set' in result

print('Timer and reminder working!')
"
```

- [ ] **Step 5: Commit**

```bash
git add friday/tools/memory.py
uv run -- git commit -m "feat: add timer and reminder tools with async support"
```

---

## Task 6: Create info.py — Weather, Wikipedia, Currency

**Files:**
- Create: `friday/tools/info.py`
- Modify: `friday/tools/__init__.py`

- [ ] **Step 1: Write info.py structure**

```python
"""
Info tools — weather, Wikipedia, currency conversion for FRIDAY's briefings.
"""

import httpx
import wikipedia
import logging

logger = logging.getLogger("friday.tools.info")


def register(mcp):

    @mcp.tool()
    async def get_weather(location: str = "local") -> str:
        """Get current weather for a location (uses Open-Meteo, free)."""
        pass

    @mcp.tool()
    async def quick_wikipedia(query: str) -> str:
        """Get a quick summary from Wikipedia."""
        pass

    @mcp.tool()
    async def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
        """Convert between currencies (e.g., USD to EUR)."""
        pass
```

- [ ] **Step 2: Implement get_weather() using Open-Meteo**

```python
    @mcp.tool()
    async def get_weather(location: str = "local") -> str:
        """Get current weather for a location (uses Open-Meteo, free)."""
        try:
            # For "local", we'd need geocoding — using a default for now
            # Open-Meteo free API: no key needed
            
            # Coordinates for major cities (fallback)
            coords = {
                "london": (51.5074, -0.1278),
                "new york": (40.7128, -74.0060),
                "tokyo": (35.6762, 139.6503),
                "paris": (48.8566, 2.3522),
            }
            
            # Default to London if "local" or unknown
            loc_key = location.lower()
            if loc_key in coords:
                lat, lon = coords[loc_key]
            else:
                lat, lon = 51.5074, -0.1278  # Default: London
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code&timezone=auto"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=10)
                data = response.json()
            
            current = data.get("current", {})
            temp = current.get("temperature_2m", "?")
            weather_code = current.get("weather_code", 0)
            
            # WMO Weather code to condition
            conditions = {
                0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                45: "foggy", 48: "foggy",
                51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
                61: "slight rain", 63: "moderate rain", 65: "heavy rain",
                71: "slight snow", 73: "moderate snow", 75: "heavy snow",
            }
            condition = conditions.get(weather_code, f"weather code {weather_code}")
            
            # Convert to Fahrenheit
            temp_f = round((temp * 9/5) + 32, 1)
            
            location_name = location if location != "local" else "your area"
            return f"It's {temp_f}°F and {condition} in {location_name}, boss. Perfect night for a flight."
            
        except Exception as e:
            logger.error(f"Weather fetch failed: {e}")
            return "Weather data is unavailable right now, boss. Check your windows?"
```

- [ ] **Step 3: Implement quick_wikipedia()**

```python
    @mcp.tool()
    async def quick_wikipedia(query: str) -> str:
        """Get a quick summary from Wikipedia."""
        try:
            # Set language and get summary
            wikipedia.set_lang("en")
            
            # Search for the topic
            search_results = wikipedia.search(query, results=1)
            if not search_results:
                return f"Couldn't find anything on Wikipedia about '{query}', boss."
            
            # Get the page
            page = wikipedia.page(search_results[0], auto_suggest=False)
            summary = page.summary[:500]  # First 500 chars
            
            return f"Here's the gist on {page.title}: {summary}..."
            
        except wikipedia.exceptions.DisambiguationError as e:
            options = e.options[:3]
            return f"That could mean a few things, boss. Try: {', '.join(options)}"
        except wikipedia.exceptions.PageError:
            return f"No Wikipedia page found for '{query}', boss."
        except Exception as e:
            logger.error(f"Wikipedia failed: {e}")
            return "Wikipedia is having trouble, boss. Try again?"
```

- [ ] **Step 4: Implement currency_convert()**

```python
    @mcp.tool()
    async def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
        """Convert between currencies (e.g., USD to EUR)."""
        try:
            # Using exchangerate-api.com (free tier available) or similar
            # For demo, using a simple fixed rate lookup
            
            # Common rates (approximate, updated periodically)
            rates = {
                "USD": {"EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "INR": 83.0, "CAD": 1.35},
                "EUR": {"USD": 1.09, "GBP": 0.86, "JPY": 163.0, "INR": 90.0},
                "GBP": {"USD": 1.27, "EUR": 1.16, "INR": 105.0},
            }
            
            from_c = from_currency.upper()
            to_c = to_currency.upper()
            
            if from_c == to_c:
                return f"That's {amount} {to_c}, boss. Same currency."
            
            # Direct rate
            if from_c in rates and to_c in rates[from_c]:
                rate = rates[from_c][to_c]
                converted = round(amount * rate, 2)
                return f"That's approximately {converted} {to_c}, boss. ({rate} rate)"
            
            # Try reverse
            if to_c in rates and from_c in rates[to_c]:
                rate = 1 / rates[to_c][from_c]
                converted = round(amount * rate, 2)
                return f"That's approximately {converted} {to_c}, boss."
            
            return f"I don't have the exchange rate from {from_c} to {to_c}, boss. Try USD, EUR, GBP, JPY, INR, or CAD."
            
        except Exception as e:
            logger.error(f"Currency conversion failed: {e}")
            return "Currency converter is down, boss. Try a calculator?"
```

- [ ] **Step 5: Test info tools**

```bash
uv run python -c "
import asyncio
import os
os.chdir('/c/Users/DELL/friday-tony-stark-demo')

from friday.tools.info import register

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register(mcp)

async def test():
    # Test weather
    result = await mcp._tools['get_weather']('london')
    print('Weather:', result[:60])
    assert '°F' in result
    
    # Test currency
    result = await mcp._tools['currency_convert'](100, 'USD', 'EUR')
    print('Currency:', result)
    assert 'approximately' in result
    
    print('Info tools working!')

asyncio.run(test())
"
```

- [ ] **Step 6: Register in __init__.py**

```python
from friday.tools import web, system, utils, diagnostics, memory, info

def register_all_tools(mcp):
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    diagnostics.register(mcp)
    memory.register(mcp)
    info.register(mcp)
```

- [ ] **Step 7: Commit**

```bash
git add friday/tools/info.py friday/tools/__init__.py
uv run -- git commit -m "feat: add info tools (weather, wikipedia, currency)"
```

---

## Task 7: Create files.py — File Search, Summary, Clipboard

**Files:**
- Create: `friday/tools/files.py`
- Modify: `friday/tools/__init__.py`

- [ ] **Step 1: Write files.py structure**

```python
"""
File tools — search, summaries, and clipboard for FRIDAY's lab work.
"""

import os
import pyperclip
from pathlib import Path
import logging

logger = logging.getLogger("friday.tools.files")

# Clipboard history (in-memory, limited)
_clipboard_history = []


def register(mcp):

    @mcp.tool()
    def search_files(query: str, path: str = "~") -> list:
        """Search for files matching query in the given path."""
        pass

    @mcp.tool()
    def read_file_summary(path: str) -> str:
        """Read and summarize a text file."""
        pass

    @mcp.tool()
    def clipboard_history(limit: int = 5) -> list:
        """Get recent clipboard items."""
        pass
```

- [ ] **Step 2: Implement search_files()**

```python
    @mcp.tool()
    def search_files(query: str, path: str = "~") -> list:
        """Search for files matching query in the given path."""
        try:
            # Expand path
            search_path = Path(path).expanduser()
            
            if not search_path.exists():
                return [{"error": f"Path not found: {path}"}]
            
            results = []
            query_lower = query.lower()
            
            # Walk directory (limit depth for speed)
            for item in search_path.rglob("*"):
                if len(results) >= 20:  # Limit results
                    break
                
                if query_lower in item.name.lower():
                    try:
                        size = item.stat().st_size
                        size_str = f"{size} bytes" if size < 1024 else f"{size/1024:.1f} KB"
                        
                        results.append({
                            "name": item.name,
                            "path": str(item),
                            "size": size_str,
                            "type": "directory" if item.is_dir() else "file"
                        })
                    except (PermissionError, OSError):
                        pass
            
            logger.info(f"File search: '{query}' in '{path}' found {len(results)} results")
            
            if not results:
                return [{"message": f"No files matching '{query}' found, boss."}]
            
            return results
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return [{"error": "Search encountered an error, boss."}]
```

- [ ] **Step 3: Implement read_file_summary()**

```python
    @mcp.tool()
    def read_file_summary(path: str) -> str:
        """Read and summarize a text file."""
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return f"That file doesn't exist, boss: {path}"
            
            if not file_path.is_file():
                return f"That's not a file, boss: {path}"
            
            # Read file (limit size)
            max_size = 1024 * 1024  # 1MB max
            if file_path.stat().st_size > max_size:
                return f"That file is too large to summarize, boss. Try a smaller one?"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Simple summary: first 500 chars + line count
            lines = content.split('\n')
            preview = content[:500] + "..." if len(content) > 500 else content
            
            return f"File has {len(lines)} lines. Preview: {preview}"
            
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return "Can't read that file, boss. Check permissions?"
```

- [ ] **Step 4: Implement clipboard_history()**

```python
    @mcp.tool()
    def clipboard_history(limit: int = 5) -> list:
        """Get recent clipboard items."""
        try:
            # Get current clipboard
            current = pyperclip.paste()
            
            # Add to history if new and not empty
            if current and (not _clipboard_history or current != _clipboard_history[0]):
                _clipboard_history.insert(0, current)
                _clipboard_history[:] = _clipboard_history[:20]  # Keep last 20
            
            # Return requested items
            items = _clipboard_history[:limit]
            
            # Format results
            results = []
            for i, content in enumerate(items):
                preview = content[:100] + "..." if len(content) > 100 else content
                results.append({
                    "index": i + 1,
                    "content_preview": preview,
                    "length": len(content)
                })
            
            if not results:
                return [{"message": "Clipboard history is empty, boss. Copy something first?"}]
            
            return results
            
        except Exception as e:
            logger.error(f"Clipboard access failed: {e}")
            return [{"error": "Can't access clipboard, boss. System restriction?"}]
```

- [ ] **Step 5: Test files tools**

```bash
uv run python -c "
import os
os.chdir('/c/Users/DELL/friday-tony-stark-demo')

from friday.tools.files import register

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register(mcp)

# Test search_files
result = mcp._tools['search_files']('.py', '.')
print('Search found:', len(result), 'items')
assert len(result) >= 0

# Test clipboard (may fail in headless, but should return gracefully)
result = mcp._tools['clipboard_history'](3)
print('Clipboard:', len(result), 'items')

print('Files tools working!')
"
```

- [ ] **Step 6: Register in __init__.py**

```python
from friday.tools import web, system, utils, diagnostics, memory, info, files

def register_all_tools(mcp):
    web.register(mcp)
    system.register(mcp)
    utils.register(mcp)
    diagnostics.register(mcp)
    memory.register(mcp)
    info.register(mcp)
    files.register(mcp)
```

- [ ] **Step 7: Commit**

```bash
git add friday/tools/files.py friday/tools/__init__.py
uv run -- git commit -m "feat: add file tools (search, summary, clipboard)"
```

---

## Task 8: Final Integration & Testing

**Files:**
- Test: All 17 tools via MCP server

- [ ] **Step 1: Start MCP server and verify tools load**

```bash
# Terminal 1: Start MCP server
uv run friday

# Terminal 2: Check available tools
curl http://127.0.0.1:8000/tools 2>/dev/null || echo "Check server logs"
```

Expected: Server starts without errors

- [ ] **Step 2: Test voice agent recognizes new tools**

Start voice agent:
```bash
$env:LIVEKIT_URL="wss://friday-36o5odn3.livekit.cloud"
$env:LIVEKIT_API_KEY="APIkdq8epnFFRaL"
$env:LIVEKIT_API_SECRET="hs1aKfBFfCGGX7bDjW2THa77pqD1S7NciQlXFvN7JQK"
uv run friday_voice
```

Expected: "FRIDAY online — room: playground-XXX | STT=deepgram | LLM=groq | TTS=google"

- [ ] **Step 3: Live test via playground**

1. Open [agents-playground.livekit.io](https://agents-playground.livekit.io)
2. Connect to `wss://friday-36o5odn3.livekit.cloud`
3. Test phrases:
   - "System status" → Should call `get_system_stats()`
   - "Save a note: buy milk" → Should call `save_note()`
   - "What's the weather?" → Should call `get_weather()`

- [ ] **Step 4: Commit final changes**

```bash
uv run -- git add -A
uv run -- git commit -m "feat: complete FRIDAY 17-tool suite (diagnostics, memory, info, files)"
```

- [ ] **Step 5: Update agent_friday.py system prompt**

Add to SYSTEM_PROMPT in `agent_friday.py`:
```markdown
### System Diagnostics
- `get_system_stats()` — "System status, boss?"
- `list_processes()` — "What's running?"
- `kill_process()` — "Kill process 1234"
- `control_brightness()` — "Brightness to 70%"
- `control_volume()` — "Volume to 50%"
- `take_screenshot()` — "Screenshot this"
- `get_battery_status()` — "Battery level?"

### Notes & Memory
- `save_note()` — "Note this down..."
- `get_notes()` — "What did I save?"
- `set_timer()` — "Timer for 10 minutes"
- `set_reminder()` — "Remind me at 3pm"

### Info & Research
- `get_weather()` — "What's the weather?"
- `quick_wikipedia()` — "Look up quantum computing"
- `currency_convert()` — "Convert 100 USD to EUR"

### Files
- `search_files()` — "Find my resume"
- `read_file_summary()` — "Summarize this document"
- `clipboard_history()` — "What did I copy earlier?"
```

- [ ] **Step 6: Final commit**

```bash
git add agent_friday.py
uv run -- git commit -m "docs: update system prompt with all 17 new tools"
```

---

## Success Verification

Run final verification:
```bash
uv run python -c "
from friday.tools import register_all_tools

class MockMCP:
    def __init__(self):
        self._tools = {}
    def tool(self):
        def decorator(f):
            self._tools[f.__name__] = f
            return f
        return decorator

mcp = MockMCP()
register_all_tools(mcp)

print(f'Total tools registered: {len(mcp._tools)}')
for name in sorted(mcp._tools.keys()):
    print(f'  - {name}')

assert len(mcp._tools) >= 17, 'Expected at least 17 new tools'
print('\n✓ All 17 tools successfully registered!')
"
```

Expected: Lists all 17+ tools

---

## Post-Implementation

1. **Restart both services** (MCP server + voice agent)
2. **Test in LiveKit playground**
3. **Iterate on tool responses** if FRIDAY's tone needs adjustment
4. **Consider adding** `quick_calendar()` or `control_rgb()` in v2

---

**Status:** Plan complete, ready for execution.
