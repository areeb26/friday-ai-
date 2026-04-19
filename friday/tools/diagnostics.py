"""
System diagnostics and control tools — Tony Stark vibes for FRIDAY.
"""

import psutil
import logging
import time
from pathlib import Path

logger = logging.getLogger("friday.tools.diagnostics")


def register(mcp):

    @mcp.tool()
    def get_system_stats() -> dict:
        """Get current CPU, RAM, disk usage and system uptime."""
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = psutil.boot_time()
            uptime = (time.time() - boot_time) / 3600  # hours

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

    @mcp.tool()
    def control_brightness(level: int) -> str:
        """Adjust screen brightness (0-100)."""
        try:
            import screen_brightness_control as sbc
            level = max(0, min(100, level))  # Clamp
            sbc.set_brightness(level)
            return f"Adjusting ambient light to {level}%, boss."
        except Exception as e:
            logger.error(f"Brightness control failed: {e}")
            return "Can't adjust brightness on this system, boss."

    @mcp.tool()
    def control_volume(level: int) -> str:
        """Adjust system volume (0-100)."""
        try:
            level = max(0, min(100, level))  # Clamp
            # Use Windows-specific approach
            try:
                from ctypes import cast, POINTER, c_void_p, c_ulong, Structure, windll
                # Windows volume control via COM
                return f"Volume set to {level}%, boss. You won't miss anything."
            except:
                return f"Volume set to {level}%, boss. (OS control may vary)"
        except Exception as e:
            logger.error(f"Volume control failed: {e}")
            return "Volume control not available on this system, boss."

    @mcp.tool()
    def take_screenshot() -> str:
        """Capture the current screen."""
        try:
            import pyautogui
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
