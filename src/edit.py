"""Unified diff patch application utilities for Pucky.

This module provides internal helper functions for applying unified diff patches.
The public API is exposed through `file.edit_file()`.
"""

import difflib
import re
from typing import TypedDict


class _Hunk(TypedDict):
    """Represents a parsed hunk from a unified diff."""

    start_line_without_old_context: int
    lines: list[str]


def apply_unified_diff(original_lines: list[str], patch: str) -> list[str]:
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
    # General hunk header pattern: @@ -start_line,line_count +start_line,line_count @@
    # Example: @@ -1,3 +1,2 @@
    # This means that the hunk starts at line 1 in the original file and has 3 lines,
    # will be replaced by 2 lines starting at line 1 in the new file.
    hunk_pattern = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

    # Parse all hunks from the patch
    hunks: list[_Hunk] = []
    i = 0
    while i < len(patch_lines):
        # Skip header lines showing file paths
        if patch_lines[i].startswith("---") or patch_lines[i].startswith("+++"):
            i += 1
            continue

        # Look for hunk header
        hunk_match = hunk_pattern.match(patch_lines[i])
        if not hunk_match:
            i += 1
            continue

        i += 1  # Move past hunk header

        # Collect hunk lines
        hunk_lines = []
        while i < len(patch_lines) and not patch_lines[i].startswith("@@"):
            hunk_lines.append(patch_lines[i])
            i += 1

        starting_line_number = int(hunk_match.group(3)) - 1  # 0-based index
        hunks.append(
            {
                "start_line_without_old_context": starting_line_number,
                "lines": hunk_lines,
            }
        )

    # Apply hunks from bottom to top to avoid line number shifts
    result_lines = original_lines.copy()
    for hunk in reversed(hunks):
        result_lines = _apply_hunk(
            result_lines,
            hunk["lines"],
            hunk["start_line_without_old_context"],
        )

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
        # Found fuzzy match with sufficient similarity (>85%)
        return best_start

    # No match found
    context_preview = "\n".join(old_context[:3])
    raise ValueError(
        f"Could not find matching context in file. Expected context:\n{context_preview}..."
    )


def _apply_hunk(
    lines: list[str],
    hunk_lines: list[str],
    start_line_without_old_context: int,
) -> list[str]:
    """Apply a single hunk to the lines.

    Args:
        lines: Current list of lines
        hunk_lines: Lines from the patch hunk (with -, +, or space prefix)
        start_line_without_old_context: Where to start in new file for insertion hunks
           (with no old context to match, e.g. "@@ -0,0 +1,3 @@")

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

    if old_context:
        # Find where the old context appears in the file to replace it with the new content
        start = _find_context_match(lines, old_context)
    else:
        # Pure insertion hunk (e.g., @@ -0,0 +1,3 @@). Use the target location
        start = min(max(start_line_without_old_context, 0), len(lines))

    # Insert new_content by placing it at the start index and keeping the rest of the lines
    consumed = len(old_context)
    new_lines = lines[:start] + new_content + lines[start + consumed :]
    return new_lines
