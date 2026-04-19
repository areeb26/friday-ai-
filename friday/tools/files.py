"""
File tools — search, summaries, and clipboard for FRIDAY's lab work.
"""

import os
from pathlib import Path
import logging
from typing import List, Dict

logger = logging.getLogger("friday.tools.files")

# Clipboard history (in-memory, limited)
_clipboard_history: List[str] = []


def register(mcp):

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
            try:
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
            except PermissionError:
                return [{"error": f"Permission denied accessing {path}"}]
            
            logger.info(f"File search: '{query}' in '{path}' found {len(results)} results")
            
            if not results:
                return [{"message": f"No files matching '{query}' found, boss."}]
            
            return results
            
        except Exception as e:
            logger.error(f"File search failed: {e}")
            return [{"error": "Search encountered an error, boss."}]

    @mcp.tool()
    def read_file_summary(path: str) -> str:
        """Read and summarize a text file."""
        try:
            file_path = Path(path).expanduser()
            
            if not file_path.exists():
                return f"That file doesn't exist, boss: {path}"
            
            if not file_path.is_file():
                return f"That's not a file, boss: {path}"
            
            # Check if it's a text file by extension
            text_extensions = {'.txt', '.md', '.py', '.json', '.csv', '.log', '.yaml', '.yml', '.xml', '.html', '.css', '.js'}
            if file_path.suffix.lower() not in text_extensions:
                return f"I can only summarize text files, boss. This is a {file_path.suffix} file."
            
            # Read file (limit size)
            max_size = 1024 * 1024  # 1MB max
            if file_path.stat().st_size > max_size:
                return f"That file is too large to summarize, boss. Try a smaller one?"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if not content.strip():
                return "That file is empty, boss. Nothing to summarize."
            
            # Simple summary: first 500 chars + line/word count
            lines = content.split('\n')
            words = content.split()
            preview = content[:500] + "..." if len(content) > 500 else content
            
            return f"File has {len(lines)} lines, {len(words)} words. Preview: {preview}"
            
        except Exception as e:
            logger.error(f"File read failed: {e}")
            return "Can't read that file, boss. Check permissions?"

    @mcp.tool()
    def clipboard_history(limit: int = 5) -> list:
        """Get recent clipboard items."""
        try:
            import pyperclip
            
            # Get current clipboard
            current = pyperclip.paste()
            
            # Add to history if new and not empty
            if current and current not in _clipboard_history:
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
