"""Unified diff patch application utilities for Pucky.

This module provides internal helper functions for applying unified diff patches.
The public API is exposed through `file.edit_file()`.
"""

import difflib
import re


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
