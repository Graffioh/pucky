"""File and directory operation utilities for Pucky.

These functions implement the core logic for:
- Reading and writing files
- Creating and deleting files/directories
- Showing file diff previews

`tools.py` exposes them as tools `_read_file`, `_write_file`,
`_delete_file`, `_create_directory`.
"""

import difflib
from pathlib import Path


def read_file(file_path: str) -> str:
    """Read a file and return its contents."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is not a file."
        return path.read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Successfully wrote to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def delete_file(file_path: str) -> str:
    """Delete a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is not a file."
        path.unlink()
        return f"Successfully deleted '{file_path}'"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def create_directory(dir_path: str) -> str:
    """Create a directory (and parent directories if needed)."""
    try:
        path = Path(dir_path)
        if path.exists():
            if path.is_dir():
                return f"Directory '{dir_path}' already exists."
            else:
                return f"Error: '{dir_path}' exists but is not a directory."
        path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory '{dir_path}'"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


def show_file_preview_with_diff(file_path: str, new_content: str) -> None:
    """Show a unified diff preview for a write operation."""
    path = Path(file_path)

    if path.exists() and path.is_file():
        try:
            old_text = path.read_text()
        except Exception:
            old_text = ""

        old_lines = old_text.splitlines()
        new_lines = new_content.splitlines()

        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"{file_path} (current)",
                tofile=f"{file_path} (new)",
                lineterm="",
            )
        )

        print("\n   Preview of changes (unified diff):")
        if diff_lines:
            for line in diff_lines:
                # Color added/removed lines similar to GitHub (green/red)
                if line.startswith("+") and not line.startswith("+++"):
                    colored = f"\033[32m{line}\033[0m"
                elif line.startswith("-") and not line.startswith("---"):
                    colored = f"\033[31m{line}\033[0m"
                else:
                    colored = line
                print(f"     {colored}")
        else:
            print("     (No changes; content is identical.)")
        print()
    else:
        print("\n   (File does not exist yet; this will create a new file.)")
        if new_content:
            print("   Content to be written:")
            for line in new_content.split("\n"):
                print(f"     {line}")
            print()
