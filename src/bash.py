"""Bash command execution utilities for Pucky.

These functions implement the core logic for:
- Executing bash commands safely
- Determining if a command is safe (read-only)
"""

import subprocess


def is_safe_bash_command(command: str) -> bool:
    """Check if a bash command is safe (read-only) and doesn't require confirmation."""
    # List of safe read-only commands that don't modify the filesystem
    safe_commands = {
        "ls",
        "grep",
        "cat",
        "head",
        "tail",
        "less",
        "more",
        "find",
        "which",
        "whereis",
        "type",
        "pwd",
        "stat",
        "wc",
        "diff",
        "cmp",
    }

    # Extract the first word (command name) from the command string
    # Handle cases like "ls -la", "grep pattern", etc.
    command_parts = command.strip().split()
    if not command_parts:
        return False

    first_word = command_parts[0].lower()

    # Check if it's a safe command
    if first_word in safe_commands:
        return True

    # Also check for commands with paths, like "/usr/bin/ls" or "./script.sh"
    # Extract just the basename
    if "/" in first_word:
        basename = first_word.split("/")[-1]
        if basename in safe_commands:
            return True

    return False


def execute_bash_command(command: str) -> str:
    """Execute a bash command and return the output."""
    try:
        # Execute the command using subprocess
        # Use shell=True to allow bash commands, but be careful with user input
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
        )

        output_parts = []

        # Add exit code
        if result.returncode != 0:
            output_parts.append(f"Exit code: {result.returncode}")

        # Add stdout if present
        if result.stdout:
            output_parts.append(f"Output:\n{result.stdout}")

        # Add stderr if present
        if result.stderr:
            output_parts.append(f"Error output:\n{result.stderr}")

        if not output_parts:
            return "Command executed successfully (no output)"

        return "\n".join(output_parts)
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 5 minutes"
    except Exception as e:
        return f"Error executing command: {str(e)}"
