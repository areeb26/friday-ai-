# FRIDAY Tools Expansion — Design Document
**Date:** 2026-04-19  
**Approach:** Full Suite (C) — System Diagnostics + Memory/Timers

---

## 1. Tools Overview (17 Total — Full JARVIS Mode)

### 🔧 System Control (Tony Stark Vibes)
| Tool | Function | FRIDAY Vibe |
|------|----------|-------------|
| `get_system_stats()` | CPU %, RAM usage, disk free, uptime | *"Your rig's running at 15% CPU, boss. All systems nominal."* |
| `list_processes()` | Top processes by CPU/memory | *"Chrome's eating 2GB RAM, boss. Want me to look closer?"* |
| `kill_process(pid)` | Terminate a process by PID | *"Terminated the process, boss. It's gone."* |
| `control_brightness(level)` | Adjust screen brightness | *"Adjusting ambient light to 70%, boss."* |
| `control_volume(level)` | System volume control | *"Volume set. You won't miss anything."* |
| `take_screenshot()` | Capture screen | *"Screenshot captured and saved."* |
| `get_battery_status()` | Laptop battery % | *"You're at 45% power, boss. Might want to plug in."* |

### 🧠 Memory & Notes
| Tool | Function | FRIDAY Vibe |
|------|----------|-------------|
| `save_note(content, tag)` | Store a note with category | *"Noted and filed under 'project ideas', boss."* |
| `get_notes(tag)` | Retrieve notes by tag | *"Here are your pending items, boss..."* |
| `set_timer(minutes, label)` | Countdown timer | *"Timer set for 10 minutes. Standing by."* |
| `set_reminder(time, message)` | One-time alerts | *"Reminder set for 3 PM tomorrow, boss."* |

### 🌐 Web & Info (Briefing Officer)
| Tool | Function | FRIDAY Vibe |
|------|----------|-------------|
| `get_weather(location)` | Current weather | *"It's 72°F and clear. Perfect night for a flight."* |
| `quick_wikipedia(query)` | Fast facts | *"Here's what I found on that, boss..."* |
| `currency_convert(amount, from, to)` | Exchange rates | *"That's approximately ₹8,340, boss."* |

### 📁 File & Data (Lab Assistant)
| Tool | Function | FRIDAY Vibe |
|------|----------|-------------|
| `search_files(query, path)` | Find files fast | *"Searching the archives... found 3 matches."* |
| `read_file_summary(path)` | TL;DR of text files | *"Summary of the document coming up..."* |
| `clipboard_history()` | Recent copies | *"Here are your last 5 clipboard items."* |

---

## 2. Architecture

```
┌─────────────────────────────────────┐
│         FRIDAY Voice Agent          │
│         (LiveKit + Groq)            │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│      MCP Server (Port 8000)         │
│  ┌─────────┐ ┌─────────┐ ┌──────┐   │
│  │  web.py │ │system.py│ │utils.py│   │
│  │ (news)  │ │(time)   │ │(calc) │   │
│  └─────────┘ └─────────┘ └──────┘   │
│  ┌─────────────────────────────────┐ │
│  │     NEW: diagnostics.py         │ │
│  │  - get_system_stats()           │ │
│  │  - list_processes()             │ │
│  │  - kill_process()               │ │
│  │  - control_brightness()         │ │
│  │  - control_volume()             │ │
│  │  - take_screenshot()              │ │
│  │  - get_battery_status()         │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │     NEW: memory.py              │ │
│  │  - save_note()                  │ │
│  │  - get_notes()                  │ │
│  │  - set_timer()                  │ │
│  │  - set_reminder()               │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │     NEW: info.py                │ │
│  │  - get_weather()                │ │
│  │  - quick_wikipedia()            │ │
│  │  - currency_convert()           │ │
│  └─────────────────────────────────┘ │
│  ┌─────────────────────────────────┐ │
│  │     NEW: files.py               │ │
│  │  - search_files()               │ │
│  │  - read_file_summary()          │ │
│  │  - clipboard_history()          │ │
│  └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**New files:**
- `friday/tools/diagnostics.py` — System diagnostics & control (7 tools)
- `friday/tools/memory.py` — Notes, timers, reminders (4 tools)
- `friday/tools/info.py` — Weather, Wikipedia, currency (3 tools)
- `friday/tools/files.py` — File search, summaries, clipboard (3 tools)

**Registration:** Add all imports to `friday/tools/__init__.py`

---

## 3. Data Flow & Storage

### System Diagnostics
- **Source:** Real-time `psutil` queries
- **Persistence:** None (live data only)
- **Update frequency:** On-demand per tool call

### Notes/Memory
- **Storage:** SQLite database (`data/friday_memory.db`)
- **Schema:**
  ```sql
  CREATE TABLE notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    tag TEXT DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  
  CREATE TABLE timers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT,
    expires_at TIMESTAMP NOT NULL,
    status TEXT DEFAULT 'active'
  );
  ```

### Timers
- **Engine:** Async background task (checks every second)
- **Trigger:** When `expires_at <= now()`, FRIDAY speaks the alert
- **Max concurrent:** 5 active timers

---

## 4. Safety & Error Handling

| Risk | Mitigation |
|------|------------|
| Kill wrong process | Require explicit PID, log action, FRIDAY confirms termination |
| Timer spam | Max 5 active timers, auto-cleanup on expiry |
| Note bloat | Auto-archive notes older than 30 days (configurable) |
| System info exposure | Local access only, no remote endpoints |
| Database corruption | SQLite WAL mode, backup on startup |

### Error Messages (FRIDAY Style)
- **Permission denied:** *"Can't terminate that process, boss. Access denied."*
- **Invalid PID:** *"That process doesn't exist, boss. Check the PID?"*
- **Timer limit:** *"I've got 5 timers running already, boss. Clear one first?"*
- **DB error:** *"My memory banks are having trouble, boss. Trying again..."*

---

## 5. Dependencies

```toml
[tool.uv.dependencies]
psutil = "^6.0.0"           # System diagnostics & process control
screen-brightness-control = "^0.24.0"  # Display brightness (Windows/Linux)
pyautogui = "^0.9.54"      # Screenshots & volume control
pyperclip = "^1.9.0"       # Clipboard access
httpx = "^0.27.0"          # Weather & Wikipedia APIs
wikipedia = "^1.4.0"       # Wikipedia summaries
```

**Built-in (no install needed):**
- `sqlite3` — Notes & reminders storage
- `subprocess` — System commands
- `os` / `pathlib` — File operations
- `datetime` — Timers & scheduling

---

## 6. Tool Specifications

### diagnostics.py (7 tools)

```python
@mcp.tool()
def get_system_stats() -> dict:
    """Get current CPU, RAM, disk usage and system uptime."""
    Returns: {
        "cpu_percent": float,
        "ram_used_gb": float,
        "ram_total_gb": float,
        "disk_free_gb": float,
        "uptime_hours": float
    }

@mcp.tool()
def list_processes(limit: int = 10) -> list:
    """List top processes by memory usage."""
    Returns: [{"pid": int, "name": str, "cpu_percent": float, "memory_mb": float}]

@mcp.tool()
def kill_process(pid: int) -> str:
    """Terminate a process by PID. Use with caution, boss."""
    Returns: "Process {pid} terminated successfully, boss." or error message

@mcp.tool()
def control_brightness(level: int) -> str:
    """Adjust screen brightness (0-100)."""
    Returns: "Adjusting ambient light to {level}%, boss."

@mcp.tool()
def control_volume(level: int) -> str:
    """Adjust system volume (0-100)."""
    Returns: "Volume set to {level}%, boss."

@mcp.tool()
def take_screenshot() -> str:
    """Capture the current screen."""
    Returns: "Screenshot captured and saved to {path}, boss."

@mcp.tool()
def get_battery_status() -> dict:
    """Get laptop battery status."""
    Returns: {"percent": int, "is_charging": bool, "time_left": str}
```

### memory.py (4 tools)

```python
@mcp.tool()
def save_note(content: str, tag: str = "general") -> str:
    """Save a note with optional category tag."""
    Returns: "Noted and filed under '{tag}', boss."

@mcp.tool()
def get_notes(tag: str = None) -> list:
    """Retrieve notes. If tag provided, filter by category."""
    Returns: [{"id": int, "content": str, "tag": str, "created_at": str}]

@mcp.tool()
async def set_timer(minutes: int, label: str = "Timer") -> str:
    """Set a countdown timer. FRIDAY will alert you when done."""
    Returns: "Timer set for {minutes} minutes. Standing by, boss."

@mcp.tool()
async def set_reminder(time: str, message: str) -> str:
    """Set a reminder for a specific time (e.g., '3pm', '15:30')."""
    Returns: "Reminder set for {time}, boss. I'll ping you."
```

### info.py (3 tools)

```python
@mcp.tool()
async def get_weather(location: str = "local") -> str:
    """Get current weather for a location (uses Open-Meteo, free)."""
    Returns: "It's {temp}°F and {condition} in {location}, boss."

@mcp.tool()
async def quick_wikipedia(query: str) -> str:
    """Get a quick summary from Wikipedia."""
    Returns: "Here's the gist: {summary}"

@mcp.tool()
async def currency_convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert between currencies (e.g., USD to EUR)."""
    Returns: "That's approximately {converted} {to_currency}, boss."
```

### files.py (3 tools)

```python
@mcp.tool()
def search_files(query: str, path: str = "~") -> list:
    """Search for files matching query in the given path."""
    Returns: [{"name": str, "path": str, "size": str}]

@mcp.tool()
def read_file_summary(path: str) -> str:
    """Read and summarize a text file."""
    Returns: "Summary: {brief_summary}"

@mcp.tool()
def clipboard_history(limit: int = 5) -> list:
    """Get recent clipboard items."""
    Returns: [{"index": int, "content_preview": str}]
```

---

## 7. Success Criteria

- [ ] `get_system_stats()` returns accurate real-time system metrics
- [ ] `list_processes()` shows top memory-consuming processes
- [ ] `kill_process()` safely terminates processes with confirmation
- [ ] `control_brightness()` adjusts screen brightness smoothly
- [ ] `control_volume()` adjusts system volume levels
- [ ] `take_screenshot()` captures and saves screen images
- [ ] `get_battery_status()` reports battery level and charging state
- [ ] `save_note()` persists notes to SQLite with tags
- [ ] `get_notes()` retrieves notes, filterable by tag
- [ ] `set_timer()` creates countdown that triggers FRIDAY voice alert
- [ ] `set_reminder()` schedules reminders for future times
- [ ] `get_weather()` fetches current weather for any location
- [ ] `quick_wikipedia()` returns concise fact summaries
- [ ] `currency_convert()` provides accurate exchange rates
- [ ] `search_files()` finds files quickly across directories
- [ ] `read_file_summary()` generates TL;DR of documents
- [ ] `clipboard_history()` tracks recent clipboard content
- [ ] All tools follow FRIDAY's briefing officer persona in error messages
- [ ] Database auto-initializes on first run
- [ ] All dependencies install cleanly via `uv`

---

## 8. Files to Modify/Create

| File | Action |
|------|--------|
| `friday/tools/diagnostics.py` | Create new — 7 system tools |
| `friday/tools/memory.py` | Create new — 4 note/timer tools |
| `friday/tools/info.py` | Create new — 3 web/info tools |
| `friday/tools/files.py` | Create new — 3 file/clipboard tools |
| `friday/tools/__init__.py` | Register all 4 new modules |
| `pyproject.toml` | Add all dependencies |
| `data/` | Create directory for SQLite DB |
| `data/friday_memory.db` | Auto-created on first run |

---

**Status:** Design complete, ready for implementation plan.
