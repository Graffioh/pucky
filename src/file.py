"""File and directory operation utilities for Pucky.

These functions implement the core logic for:
- Reading and writing files
- Creating and deleting files/directories
- Showing file diff previews

`tools.py` exposes them as tools `_read_file`, `_write_file`,
`_edit_file`, `_delete_file`, `_create_directory`.
"""

import difflib
import re
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


def edit_file(file_path: str, patch: str) -> str:
    """Apply a unified diff patch to a file.

    Args:
        file_path: Path to the file to edit
        patch: Unified diff patch string to apply

    Returns:
        Success message or error description
    """
    try:
        path = Path(file_path)

        # Read current file content
        if path.exists() and path.is_file():
            current_lines = path.read_text().splitlines(keepends=False)
        elif path.exists():
            return f"Error: '{file_path}' exists but is not a file."
        else:
            # File doesn't exist, start with empty content
            current_lines = []

        # Parse and apply the patch
        new_lines = _apply_unified_diff(current_lines, patch)

        # Write the modified content back
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(new_lines) + ("\n" if new_lines else ""))

        return f"Successfully applied patch to '{file_path}'"
    except ValueError as e:
        return f"Error applying patch: {str(e)}"
    except Exception as e:
        return f"Error editing file: {str(e)}"


def _apply_unified_diff(original_lines: list[str], patch: str) -> list[str]:
    """Apply a unified diff patch to a list of lines.

    Args:
        original_lines: List of lines from the original file
        patch: Unified diff patch string

    Returns:
        Modified list of lines

    Raises:
        ValueError: If the patch cannot be applied
    """
    patch_lines = patch.splitlines()
    hunk_pattern = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

    # Parse all hunks from the patch
    hunks = []
    i = 0
    while i < len(patch_lines):
        # Skip header lines
        if patch_lines[i].startswith("---") or patch_lines[i].startswith("+++"):
            i += 1
            continue

        # Look for hunk header
        match = hunk_pattern.match(patch_lines[i])
        if not match:
            i += 1
            continue

        i += 1  # Move past hunk header

        # Collect hunk lines
        hunk_lines = []
        while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
            hunk_lines.append(patch_lines[i])
            i += 1

        hunks.append(hunk_lines)

    # Apply hunks from bottom to top to avoid line number shifts
    result_lines = original_lines.copy()
    for hunk_lines in reversed(hunks):
        result_lines = _apply_hunk(result_lines, hunk_lines)

    return result_lines


def _find_context_match(lines: list[str], old_context: list[str]) -> int:
    """Find where the old context appears in the file using difflib for fuzzy matching.

    Args:
        lines: Current file lines
        old_context: Context lines from the patch to match

    Returns:
        The 0-based index where the context starts

    Raises:
        ValueError: If the context cannot be found
    """
    # First try exact match
    for i in range(len(lines) - len(old_context) + 1):
        if lines[i : i + len(old_context)] == old_context:
            return i

    # If no exact match, use difflib for fuzzy matching
    best_ratio = 0.85  # Require at least 85% similarity
    best_start = None

    for i in range(max(0, len(lines) - len(old_context) + 1)):
        candidate = lines[i : i + len(old_context)]
        if len(candidate) < len(old_context):
            continue
        ratio = difflib.SequenceMatcher(None, old_context, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_start = i

    if best_start is not None:
        # Verify the fuzzy match is correct (check all context lines)
        for i in range(len(old_context)):
            if best_start + i >= len(lines) or lines[best_start + i] != old_context[i]:
                context_preview = "\n".join(old_context[:3])
                got_line = lines[best_start + i][:50] if best_start + i < len(lines) else "EOF"
                raise ValueError(
                    f"Context mismatch at line {best_start + i + 1}: "
                    f"expected '{old_context[i][:50]}...', got '{got_line}...'"
                )
        return best_start

    # No match found
    context_preview = "\n".join(old_context[:3])
    raise ValueError(
        f"Could not find matching context in file. Expected context:\n{context_preview}..."
    )


def _apply_hunk(lines: list[str], hunk_lines: list[str]) -> list[str]:
    """Apply a single hunk to the lines.

    Args:
        lines: Current list of lines
        hunk_lines: Lines from the patch hunk (with -, +, or space prefix)

    Returns:
        Modified list of lines

    Raises:
        ValueError: If the hunk cannot be applied
    """
    # Extract old context (lines to match) and new content (lines to insert)
    old_context = []
    new_content = []
    for hunk_line in hunk_lines:
        if hunk_line.startswith(" "):
            # Context line - appears in both old and new
            old_context.append(hunk_line[1:])
            new_content.append(hunk_line[1:])
        elif hunk_line.startswith("-"):
            # Deleted line - only in old
            old_context.append(hunk_line[1:])
        elif hunk_line.startswith("+"):
            # Added line - only in new
            new_content.append(hunk_line[1:])
        elif hunk_line.strip() == "":
            # Empty line - skip
            continue
        else:
            raise ValueError(f"Invalid hunk line format: {hunk_line[:50]}")

    if not old_context:
        # No context to match - this is unusual but handle it
        raise ValueError("Hunk has no context lines to match")

    # Find where the old context appears in the file
    start = _find_context_match(lines, old_context)

    consumed = len(old_context)

    # Build the result: lines before + new content + lines after
    new_lines = lines[:start] + new_content + lines[start + consumed :]
    return new_lines


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
