"""File operation tools for the code agent."""

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
