"""Tool execution and orchestration for the code agent."""

import re
from typing import TypedDict

from .bash import execute_bash_command, is_safe_bash_command
from .context import grep_search, scan_codebase
from .file import (
    create_directory,
    delete_file,
    edit_file,
    read_file,
    write_file,
)
from .utils import get_user_input, syntax_highlight


class ToolResult(TypedDict):
    """Structure of a tool execution result."""

    tool_type: str
    result: str
    parameters: dict[str, str]


class ToolCall(TypedDict):
    """Structure of a parsed tool call."""

    call_type: str
    parameters: dict[str, str]
    raw_xml: str


def _read_file(file_path: str) -> str:
    """Adapter that delegates to file.read_file."""
    return read_file(file_path)


def _write_file(file_path: str, content: str) -> str:
    """Adapter that delegates to file.write_file."""
    return write_file(file_path, content)


def _edit_file(file_path: str, patch: str) -> str:
    """Adapter that delegates to file.edit_file."""
    return edit_file(file_path, patch)


def _delete_file(file_path: str) -> str:
    """Adapter that delegates to file.delete_file."""
    return delete_file(file_path)


def _create_directory(dir_path: str) -> str:
    """Adapter that delegates to file.create_directory."""
    return create_directory(dir_path)


def _scan_codebase(root_path: str) -> str:
    """Adapter that delegates to context.scan_codebase."""
    return scan_codebase(root_path)


def _grep_search(root_path: str, query: str, max_results: str = "80") -> str:
    """Adapter that delegates to context.grep_search."""
    return grep_search(root_path, query, max_results=max_results)


def _show_edit_preview(file_path: str, patch: str) -> None:
    """Show a preview of the patch that will be applied to a file."""
    from pathlib import Path

    path = Path(file_path)

    if path.exists() and path.is_file():
        try:
            current_lines = path.read_text().splitlines(keepends=False)
        except Exception:
            current_lines = []

        # Show the patch that will be applied
        print("\n   Patch to apply:")
        for line in patch.splitlines():
            # Color added/removed lines similar to GitHub (green/red)
            if line.startswith("+") and not line.startswith("+++"):
                colored = f"\033[32m{line}\033[0m"
            elif line.startswith("-") and not line.startswith("---"):
                colored = f"\033[31m{line}\033[0m"
            else:
                colored = line
            print(f"     {colored}")

        # Try to compute what the file will look like after applying the patch
        try:
            from .file import _apply_unified_diff

            new_lines = _apply_unified_diff(current_lines, patch)
            new_content = "\n".join(new_lines) + ("\n" if new_lines else "")

            # Show the computed diff
            print("\n   Resulting file changes (unified diff):")
            from .file import show_file_preview_with_diff

            show_file_preview_with_diff(file_path, new_content)
        except Exception as e:
            print(f"\n   (Could not preview result: {str(e)})")
            print()
    else:
        print("\n   (File does not exist yet; this will create a new file.)")
        print("   Patch to apply:")
        for line in patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                colored = f"\033[32m{line}\033[0m"
            elif line.startswith("-") and not line.startswith("---"):
                colored = f"\033[31m{line}\033[0m"
            else:
                colored = line
            print(f"     {colored}")
        print()


def _execute_bash_command(command: str) -> str:
    """Adapter that delegates to bash.execute_bash_command."""
    return execute_bash_command(command)


def _format_operation_description(tool_type: str, parameters: dict[str, str]) -> str:
    """Return a one-line human description for an operation."""
    if tool_type == "read_file":
        file_path = parameters.get("file_path", "unknown")
        return f"📖 Reading file: {file_path}"
    if tool_type == "write_file":
        file_path = parameters.get("file_path", "unknown")
        return f"✏️  Writing into file: {file_path}"
    if tool_type == "edit_file":
        file_path = parameters.get("file_path", "unknown")
        return f"🔧 Editing file with patch: {file_path}"
    if tool_type == "delete_file":
        file_path = parameters.get("file_path", "unknown")
        return f"🗑️  Deleting file: {file_path}"
    if tool_type == "create_directory":
        dir_path = parameters.get("dir_path", "unknown")
        return f"📁 Creating directory: {dir_path}"
    if tool_type == "execute_bash_command":
        command = parameters.get("command", "unknown")
        return f"⚡ Executing bash command: {command}"
    if tool_type == "scan_codebase":
        root_path = parameters.get("root_path", ".")
        return f"🗺️  Scanning codebase structure at: {root_path}"
    if tool_type == "grep_search":
        root_path = parameters.get("root_path", ".")
        query = parameters.get("query", "")
        return f"🔍 Searching codebase at: {root_path} for: {query!r}"
    return f"❓ Unknown operation: {tool_type}"


def parse_tool_calls(text: str) -> list[ToolCall]:
    """
    Parse XML tool calls from agent response text.

    Args:
        text: The response text that may contain XML tool calls

    Returns:
        A list of dictionaries, each containing:
        - 'type': The tool type (e.g., 'read_file', 'write_file')
        - 'parameters': A dict of parameter name-value pairs
        - 'raw_xml': The raw XML string for this tool call
    """
    tool_calls = []

    # Find all tool_call blocks using regex (more flexible than strict XML parsing)
    # This pattern matches <tool_call>...</tool_call> blocks, including multiline
    pattern = r"<tool_call\s+type=\"([^\"]+)\">(.*?)</tool_call>"
    matches = re.findall(pattern, text, re.DOTALL)

    for tool_type, params_content in matches:
        parameters = {}

        # Extract parameters from the tool call block
        param_pattern = r'<parameter\s+name="([^"]+)">(.*?)</parameter>'
        param_matches = re.findall(param_pattern, params_content, re.DOTALL)

        for param_name, param_value in param_matches:
            parameters[param_name] = param_value.strip()

        # Reconstruct the full XML for this tool call
        raw_xml = f'<tool_call type="{tool_type}">{params_content}</tool_call>'

        tool_calls.append(
            {
                "call_type": tool_type,
                "parameters": parameters,
                "raw_xml": raw_xml,
            }
        )

    return tool_calls


def execute_tool_calls(tool_calls: list[ToolCall]) -> list[ToolResult]:
    """Execute a list of tool calls and return the results.

    Args:
        tool_calls: A list of tool calls to execute

    Returns:
        A list of tool results
    """
    tool_results = []
    if tool_calls:
        # Map tool types to their functions
        tool_map = {
            "read_file": _read_file,
            "write_file": _write_file,
            "edit_file": _edit_file,
            "delete_file": _delete_file,
            "create_directory": _create_directory,
            "execute_bash_command": _execute_bash_command,
            "scan_codebase": _scan_codebase,
            "grep_search": _grep_search,
        }

        # Print operations that will be performed
        print("\n🔧 Operations to perform:")
        for tool_call in tool_calls:
            tool_type = tool_call["call_type"]
            parameters = tool_call["parameters"]

            # Format operation description
            description = _format_operation_description(tool_type, parameters)
            print(f"  {description}")
        print()

        total_ops = len(tool_calls)

        for index, tool_call in enumerate(tool_calls, start=1):
            tool_type = tool_call["call_type"]
            parameters = tool_call["parameters"]

            # Execute read-only operations immediately without confirmation
            # These are: read_file, scan_codebase, grep_search
            read_only_ops = {"read_file", "scan_codebase", "grep_search"}

            # Check if this is a safe bash command that doesn't need confirmation
            is_safe_bash = False
            if tool_type == "execute_bash_command":
                command = parameters.get("command", "")
                is_safe_bash = is_safe_bash_command(command)

            # Otherwise, ask for confirmation
            # Bash commands require confirmation for security, except safe read-only ones
            if tool_type not in read_only_ops and not is_safe_bash:
                while True:
                    description = _format_operation_description(tool_type, parameters)
                    print(f"\n❓ Confirm operation {index}/{total_ops}:")
                    print(f"   {description}")

                    # For write operations, show a simple preview (no diff since it's for new files)
                    if tool_type == "write_file":
                        file_path = parameters.get("file_path", "unknown")
                        content = parameters.get("content", "")
                        from pathlib import Path

                        path = Path(file_path)
                        if path.exists() and path.is_file():
                            print(
                                f"\n   ⚠️  Warning: File '{file_path}' "
                                "already exists. This will overwrite it."
                            )
                        else:
                            print(f"\n   📝 Creating new file: {file_path}")
                        if content:
                            line_count = len(content.splitlines())
                            print(f"   Content: {line_count} line(s)")

                    # For edit operations, show the patch and preview
                    if tool_type == "edit_file":
                        file_path = parameters.get("file_path", "unknown")
                        patch = parameters.get("patch", "")
                        _show_edit_preview(file_path, patch)

                    answer = get_user_input("   Proceed? [y]es / [n]o / [q]uit: ")
                    if answer is None:
                        user_choice = "q"
                    else:
                        user_choice = answer.strip().lower()

                    if user_choice in ("y", "yes"):
                        break
                    if user_choice in ("n", "no"):
                        tool_results.append(
                            {
                                "tool_type": tool_type,
                                "result": "Operation skipped by user",
                                "parameters": parameters,
                            }
                        )
                        # Skip execution, go to next tool_call
                        break
                    if user_choice in ("q", "quit"):
                        print("\n⏹️  Stopping remaining operations at your request.\n")
                        return tool_results

                    print("   Please answer with 'y', 'n', or 'q'.")

                # If the user chose "no", we already added a result
                # and should skip executing
                if (
                    tool_results
                    and tool_results[-1]["tool_type"] == tool_type
                    and tool_results[-1]["result"] == "Operation skipped by user"
                ):
                    continue

            if tool_type not in tool_map:
                result = (
                    f"Error: Unknown tool type '{tool_type}'. "
                    f"Available tools: {', '.join(tool_map.keys())}"
                )
            else:
                try:
                    # Execute the tool function
                    tool_func = tool_map[tool_type]
                    result = tool_func(**parameters)
                except TypeError as e:
                    result = (
                        f"Error: Invalid parameters for {tool_type}. "
                        f"Required parameters not provided. {str(e)}"
                    )
                except Exception as e:
                    result = f"Error executing {tool_type}: {str(e)}"

            tool_results.append(
                {
                    "tool_type": tool_type,
                    "result": result,
                    "parameters": parameters,
                }
            )

    return tool_results


def print_tool_results_summary(tool_results: list[ToolResult]) -> None:
    """Print a summary of the tool results."""
    print("\n🔧 Tool execution results:")
    for tool_result in tool_results:
        tool_type = tool_result["tool_type"]
        result = tool_result["result"]
        parameters = tool_result["parameters"]

        display_text = result
        if tool_type == "read_file":
            file_path = parameters.get("file_path")
            display_text = syntax_highlight(result, file_path=file_path)

        display_text = display_text.rstrip("\n")
        if "\n" in display_text:
            print(f"  {tool_type}:")
            for line in display_text.splitlines():
                print(f"    {line}")
        else:
            print(f"  {tool_type}: {display_text}")
    print()
