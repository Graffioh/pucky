"""Async CLI actions that augment the next LLM request context."""

from __future__ import annotations

from .context import use_file_for_context


def _use_file_for_context(
    path_str: str, conversation_history: list[dict[str, str]]
) -> None:
    """Adapter that delegates to context.use_file_for_context."""
    use_file_for_context(path_str, conversation_history)


def print_async_help() -> None:
    """Print the list of async (local) commands."""
    print(
        "\n⚙️  Async actions (without calling the LLM):\n"
        "  @file <path>   – stage a file so the agent sees its contents next turn\n"
        "  @help          – show this help message\n"
        "\n"
    )


def handle_async_action(
    raw_input: str, conversation_history: list[dict[str, str]]
) -> bool:
    """Handle commands that start with '@' without pinging the model."""
    command, _, arguments = raw_input[1:].partition(" ")
    command = command.strip().lower()
    arguments = arguments.strip()

    if command in {"file", "f"}:
        _use_file_for_context(arguments, conversation_history)
        return True

    if command in {"help", "commands", "?"}:
        print_async_help()
        return True

    if not command:
        print("\n⚠️  Async commands need a name, e.g., '@file README.md'.")
    else:
        print(f"\n⚠️  Unknown async action '@{command}'. Type '@help' for the list.")
    return True


__all__ = [
    "handle_async_action",
    "print_async_help",
]
