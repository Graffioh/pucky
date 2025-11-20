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
        "  @prompt <text>       – append instructions to the dynamic system prompt\n"
        "  @show_prompt         – show the current system prompt\n"
        "  @reset_prompt        – clear the dynamic system prompt\n"
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


def _update_prompt(instruction: str, dynamic_instructions: list[str]) -> None:
    """Append a new instruction to the dynamic system prompt (in-memory)."""
    try:
        dynamic_instructions.append(instruction)
        print(f"\n🧠 Instruction added to system prompt: {instruction}\n")
    except Exception as e:
        print(f"\n❌ Error updating instructions: {e}\n")


def _reset_prompt(dynamic_instructions: list[str]) -> None:
    """Clear the dynamic system prompt (in-memory)."""
    try:
        dynamic_instructions.clear()
        print("\n🧠 Dynamic system prompt cleared.\n")
    except Exception as e:
        print(f"\n❌ Error clearing instructions: {e}\n")


def _print_system_prompt(prompt: str | None) -> None:
    """Print the current system prompt."""
    if not prompt:
        print("\n⚠️  System prompt is empty or unavailable.\n")
        return
    print(f"\n📜 Current System Prompt:\n\n{prompt}\n")


def handle_async_action(
    raw_input: str,
    conversation_history: list[dict[str, str]],
    system_prompt: str | None = None,
    max_tokens: int | None = None,
    dynamic_instructions: list[str] | None = None,
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

    if command in {"tts"}:
        speak_latest_response(conversation_history)
        return True

    if command in {"prompt", "p"}:
        if not arguments:
            print("\n⚠️  Usage: @prompt <instruction text>")
        elif dynamic_instructions is not None:
            _update_prompt(arguments, dynamic_instructions)
        else:
            print("\n❌ Error: Dynamic instructions not available.\n")
        return True

    if command in {"show_prompt", "sp"}:
        _print_system_prompt(system_prompt)
        return True

    if command in {"reset_prompt", "reset"}:
        if dynamic_instructions is not None:
            _reset_prompt(dynamic_instructions)
        else:
            print("\n❌ Error: Dynamic instructions not available.\n")
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
