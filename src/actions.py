"""Async CLI actions that augment the next LLM request context."""

from __future__ import annotations

from .context import estimate_tokens_for_history, scan_codebase, use_file_for_context
from .tts import speak_latest_response


def print_async_help() -> None:
    """Print the list of async (local) commands."""
    print(
        "\n⚙️  Async actions (without calling the LLM):\n"
        "  @file <path_to_file> – stage a file so the agent sees its contents next turn\n"
        "  @tree [path]         – show the file-tree project structure\n"
        "  @context             – print the current context length\n"
        "  @tts                 – speak the latest agent response using elevenlabs text-to-speech\n"
        "  @help                – show this help message\n"
        "\n"
    )


def _use_file_for_context(path_str: str, conversation_history: list[dict[str, str]]) -> None:
    """Adapter that delegates to context.use_file_for_context."""
    use_file_for_context(path_str, conversation_history)


async def _print_context_length(
    conversation_history: list[dict[str, str]],
    system_prompt: str | None = None,
    max_tokens: int | None = None,
) -> None:
    """Print the current context length in tokens."""
    token_count = estimate_tokens_for_history(conversation_history, system_prompt=system_prompt)
    if max_tokens is not None:
        print(f"\n📊 Current context length: {token_count:,} / {max_tokens:,} tokens\n")
    else:
        print(f"\n📊 Current context length: {token_count:,} tokens\n")


def _print_tree(path_str: str = ".") -> None:
    """Print the file-tree project structure."""
    result = scan_codebase(path_str)
    print(f"\n{result}\n")


def handle_async_action(
    raw_input: str,
    conversation_history: list[dict[str, str]],
    system_prompt: str | None = None,
    max_tokens: int | None = None,
) -> bool:
    """Handle commands that start with '@' without pinging the model."""
    command, _, arguments = raw_input[1:].partition(" ")
    command = command.strip().lower()
    arguments = arguments.strip()

    if command in {"file", "f"}:
        _use_file_for_context(arguments, conversation_history)
        return True

    if command in {"tree", "t"}:
        path = arguments if arguments else "."
        _print_tree(path)
        return True

    if command in {"context", "c"}:
        import asyncio

        asyncio.run(_print_context_length(conversation_history, system_prompt, max_tokens))
        return True

    if command in {"help", "commands", "?"}:
        print_async_help()
        return True

    if command in {"tts"}:
        speak_latest_response(conversation_history)
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
