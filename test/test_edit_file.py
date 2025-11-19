#!/usr/bin/env python3
"""Unit tests for edit_file functionality."""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path to import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.edit import edit_file


def test_simple_edit():
    """Test a simple edit operation."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line1\nline2\nline3\n")
        temp_path = f.name

    try:
        patch = """@@ -1,3 +1,4 @@
 line1
-line2
+new line2
+added line
 line3"""

        result = edit_file(temp_path, patch)
        assert "Successfully" in result

        # Verify the file was modified correctly
        content = Path(temp_path).read_text()
        expected = "line1\nnew line2\nadded line\nline3\n"
        assert content == expected, f"Expected:\n{expected}\nGot:\n{content}"
        print("✓ Simple edit test passed")
    finally:
        Path(temp_path).unlink()


def test_context_mismatch():
    """Test that context mismatch is detected."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line1\nline2\nline3\n")
        temp_path = f.name

    try:
        # Patch expects "wrong" but file has "line2"
        patch = """@@ -1,3 +1,3 @@
 line1
-wrong
+new line
 line3"""

        result = edit_file(temp_path, patch)
        assert "Error" in result or "mismatch" in result.lower()
        print("✓ Context mismatch test passed")
    finally:
        Path(temp_path).unlink()


def test_multiple_hunks():
    """Test applying multiple hunks."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line1\nline2\nline3\nline4\nline5\n")
        temp_path = f.name

    try:
        patch = """@@ -1,3 +1,3 @@
 line1
-line2
+new2
 line3
@@ -4,2 +4,2 @@
 line4
-line5
+new5"""

        result = edit_file(temp_path, patch)
        assert "Successfully" in result

        content = Path(temp_path).read_text()
        expected = "line1\nnew2\nline3\nline4\nnew5\n"
        assert content == expected, f"Expected:\n{expected}\nGot:\n{content}"
        print("✓ Multiple hunks test passed")
    finally:
        Path(temp_path).unlink()


def test_delete_only():
    """Test deleting lines without adding."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("line1\nline2\nline3\n")
        temp_path = f.name

    try:
        patch = """@@ -1,3 +1,2 @@
 line1
-line2
 line3"""

        result = edit_file(temp_path, patch)
        assert "Successfully" in result

        content = Path(temp_path).read_text()
        expected = "line1\nline3\n"
        assert content == expected, f"Expected:\n{expected}\nGot:\n{content}"
        print("✓ Delete-only test passed")
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    print("Running edit_file tests...\n")
    test_simple_edit()
    test_context_mismatch()
    test_multiple_hunks()
    test_delete_only()
    print("\n✅ All tests passed!")
