"""Codebase scanning and search utilities for Pucky.

These functions implement the core logic for:
- Getting a high-level view of the project structure
- Searching for text within code/text files

Via .gitignore patterns, we can ignore directories that are not code related.

`tools.py` exposes them as tools `_scan_codebase` and `_search_codebase`.
"""

from __future__ import annotations

import os
from pathlib import Path

import pathspec

# Default directories that should always be skipped (they are either VCS metadata
# or heavyweight dependency/build folders that shouldn't be scanned).
_DEFAULT_SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".cache",
}

# Common text/code file extensions
_CODE_FILE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
    ".txt",
    ".html",
    ".css",
    ".scss",
    ".go",
    ".rs",
    ".java",
    ".c",
    ".h",
    ".cpp",
    ".cc",
    ".ini",
    ".cfg",
    ".env",
}


def _load_gitignore_specs(root: Path):
    """
    Load and combine .gitignore files found in the repository.

    Patterns from nested .gitignore files are prefixed with their directory so
    they have the same scope as in Git.
    """
    gitignore_patterns: list[str] = []

    for dirpath, dirnames, _ in os.walk(root):
        # Skip heavyweight / dependency dirs while collecting patterns
        dirnames[:] = [d for d in dirnames if d not in _DEFAULT_SKIP_DIRS]

        gitignore_path = Path(dirpath) / ".gitignore"
        if not gitignore_path.exists() or not gitignore_path.is_file():
            continue

        rel_dir = Path(dirpath).relative_to(root)
        if rel_dir in (Path("."), Path()):
            prefix = ""
        else:
            rel_str = str(rel_dir).replace("\\", "/")
            prefix = f"{rel_str}/"

        try:
            with gitignore_path.open("r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    pattern = line.strip()
                    if not pattern or pattern.startswith("#"):
                        continue

                    negated = pattern.startswith("!")
                    core = pattern[1:] if negated else pattern

                    if core.startswith("/"):
                        scoped = core.lstrip("/")
                    else:
                        scoped = f"{prefix}{core}" if prefix else core

                    gitignore_patterns.append(f"{'!' if negated else ''}{scoped}")
        except (OSError, UnicodeDecodeError):
            continue

    if not gitignore_patterns:
        return None

    try:
        return pathspec.PathSpec.from_lines("gitwildmatch", gitignore_patterns)
    except Exception:
        return None


def _is_ignored_by_gitignore(
    path: Path,
    root: Path,
    gitignore_spec,
) -> bool:
    """
    Check if a path should be ignored based on .gitignore patterns.

    Args:
        path: The absolute path to check
        root: The repository root (absolute)
        gitignore_spec: The PathSpec object from _load_gitignore_specs, or None

    Returns:
        True if the path should be ignored, False otherwise
    """
    if gitignore_spec is None or pathspec is None:
        return False

    try:
        # Get relative path from root
        rel_path = path.relative_to(root)
        # Convert to forward slashes (gitignore convention)
        rel_str = str(rel_path).replace("\\", "/")
        # Check if it matches any ignore pattern
        return gitignore_spec.match_file(rel_str)  # type: ignore[union-attr]
    except (ValueError, Exception):
        # If path is not relative to root or other error, don't ignore
        return False


def _should_ignore_path(
    path: Path, root: Path, gitignore_spec, is_dir: bool = False
) -> bool:
    """
    Check if a path should be ignored (combines hardcoded ignores and .gitignore).

    Args:
        path: The absolute path to check
        root: The repository root (absolute)
        gitignore_spec: The PathSpec object from _load_gitignore_specs, or None
        is_dir: Whether the path is a directory

    Returns:
        True if the path should be ignored, False otherwise
    """
    # Check default skip directories first
    if is_dir and path.name in _DEFAULT_SKIP_DIRS:
        return True

    # Check .gitignore patterns
    return _is_ignored_by_gitignore(path, root, gitignore_spec)


def scan_codebase(root_path: str) -> str:
    """
    Intelligently scan the codebase structure without reading every file.

    - Skips common non-code / cache / dependency directories
    - Focuses on text and source-code file types
    - Returns a high-level tree and file-type summary
    """
    try:
        root = Path(root_path).expanduser().resolve()
    except Exception as e:
        return f"Error: Invalid root_path '{root_path}': {e}"

    if not root.exists():
        return f"Error: Path '{root}' does not exist."
    if not root.is_dir():
        return f"Error: Path '{root}' is not a directory."

    # Load .gitignore patterns if available
    gitignore_spec = _load_gitignore_specs(root)

    max_files = 400  # avoid dumping huge trees
    files_by_dir: dict[str, list[str]] = {}
    type_counts: dict[str, int] = {}
    total_files = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out ignored directories in-place so os.walk skips them
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_ignore_path(
                Path(dirpath) / d, root, gitignore_spec, is_dir=True
            )
        ]

        rel_dir = str(Path(dirpath).relative_to(root)) or "."

        for filename in filenames:
            if total_files >= max_files:
                break

            path = Path(dirpath) / filename
            ext = path.suffix.lower()

            # Check if ignored (hardcoded + .gitignore)
            if _should_ignore_path(path, root, gitignore_spec):
                continue

            # Skip non-code files by extension
            if ext and ext not in _CODE_FILE_EXTENSIONS:
                continue

            # Quick size guard: skip very large files
            try:
                if path.stat().st_size > 512 * 1024:  # > 512 KB
                    continue
            except OSError:
                continue

            files_by_dir.setdefault(rel_dir, []).append(filename)

            # Track type counts
            type_key = ext or "<no-ext>"
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
            total_files += 1

        if total_files >= max_files:
            break

    if not files_by_dir:
        return f"No interesting files found under '{root}'."

    lines: list[str] = []
    lines.append(f"Codebase scan (root: {root})")
    lines.append("")
    lines.append("Directories and key files (truncated):")

    for rel_dir in sorted(files_by_dir.keys()):
        lines.append(f"- {rel_dir}/")
        # Show up to 10 files per directory
        dir_files = sorted(files_by_dir[rel_dir])
        for filename in dir_files[:10]:
            lines.append(f"  - {filename}")
        if len(dir_files) > 10:
            lines.append(f"  - ... ({len(dir_files) - 10} more files)")

    lines.append("")
    lines.append("File types summary:")
    for ext, count in sorted(type_counts.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {ext}: {count} file(s)")

    if total_files >= max_files:
        lines.append("")
        lines.append(
            f"Note: Stopped after {max_files} files to avoid scanning the entire tree."
        )

    return "\n".join(lines)


def search_codebase(root_path: str, query: str, max_results: int | str = 80) -> str:
    """
    Search for a text query inside the codebase without blindly reading all files.

    - Skips common non-code / cache / dependency directories
    - Restricts search to common text/code file types
    - Applies file size limits and caps total matches
    - Returns compact, contextual snippets for each match
    """
    if not query:
        return "Error: 'query' parameter must be a non-empty string."

    try:
        root = Path(root_path).expanduser().resolve()
    except Exception as e:
        return f"Error: Invalid root_path '{root_path}': {e}"

    if not root.exists():
        return f"Error: Path '{root}' does not exist."
    if not root.is_dir():
        return f"Error: Path '{root}' is not a directory."

    try:
        max_results_int = int(max_results)
        if max_results_int <= 0:
            max_results_int = 80
    except (TypeError, ValueError):
        max_results_int = 80

    # Load .gitignore patterns if available
    gitignore_spec = _load_gitignore_specs(root)

    matches: list[str] = []
    total_matches = 0
    per_file_limit = 5

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if not _should_ignore_path(
                Path(dirpath) / d, root, gitignore_spec, is_dir=True
            )
        ]

        for filename in filenames:
            if total_matches >= max_results_int:
                break

            path = Path(dirpath) / filename
            ext = path.suffix.lower()

            # Check if ignored (hardcoded + .gitignore)
            if _should_ignore_path(path, root, gitignore_spec):
                continue

            # Skip non-code files by extension
            if ext and ext not in _CODE_FILE_EXTENSIONS:
                continue

            try:
                if path.stat().st_size > 512 * 1024:  # > 512 KB
                    continue
            except OSError:
                continue

            try:
                with path.open("r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except (OSError, UnicodeDecodeError):
                continue

            file_match_count = 0
            rel_path = str(path.relative_to(root))

            for idx, line in enumerate(lines, start=1):
                if (
                    total_matches >= max_results_int
                    or file_match_count >= per_file_limit
                ):
                    break

                if query in line:
                    snippet = line.rstrip("\n")
                    if len(snippet) > 200:
                        snippet = snippet[:200] + "..."
                    matches.append(f"{rel_path}:{idx}: {snippet}")
                    total_matches += 1
                    file_match_count += 1

        if total_matches >= max_results_int:
            break

    if not matches:
        return f"No matches for '{query}' under '{root}'."

    header = [
        f"Search results for '{query}' (root: {root}):",
        f"- Total matches: {total_matches}",
        f"- Max reported matches: {max_results_int}",
        "",
    ]

    if total_matches > max_results_int:
        footer = [
            "",
            f"Note: Showing only the first {max_results_int} matches. "
            "Refine your query or search a narrower directory if needed.",
        ]
    else:
        footer = []

    return "\n".join(header + matches + footer)
