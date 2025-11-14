"""Tool execution and orchestration for the code agent."""

import re
import subprocess
from typing import TypedDict

from .file import (
    create_directory,
    delete_file,
    read_file,
    show_file_preview_with_diff,
    write_file,
)
from .scanner import scan_codebase, search_codebase
from .utils import get_user_input


class ToolResult(TypedDict):
    """Structure of a tool execution result."""

    tool_type: str
    result: str


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


def _delete_file(file_path: str) -> str:
    """Adapter that delegates to file.delete_file."""
    return delete_file(file_path)


def _create_directory(dir_path: str) -> str:
    """Adapter that delegates to file.create_directory."""
    return create_directory(dir_path)


def _scan_codebase(root_path: str) -> str:
    """Adapter that delegates to scanner.scan_codebase."""
    return scan_codebase(root_path)


def _search_codebase(root_path: str, query: str, max_results: str = "80") -> str:
    """Adapter that delegates to scanner.search_codebase."""
    return search_codebase(root_path, query, max_results=max_results)


def _show_file_preview_with_diff(file_path: str, new_content: str) -> None:
    """Adapter that delegates to file.show_file_preview_with_diff."""
    show_file_preview_with_diff(file_path, new_content)


def _execute_bash_command(command: str) -> str:
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


def _format_operation_description(tool_type: str, parameters: dict[str, str]) -> str:
    """Return a one-line human description for an operation."""
    if tool_type == "read_file":
        file_path = parameters.get("file_path", "unknown")
        return f"📖 Reading file: {file_path}"
    if tool_type == "write_file":
        file_path = parameters.get("file_path", "unknown")
        return f"✏️  Writing into file: {file_path}"
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
    if tool_type == "search_codebase":
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
            "delete_file": _delete_file,
            "create_directory": _create_directory,
            "execute_bash_command": _execute_bash_command,
            "scan_codebase": _scan_codebase,
            "search_codebase": _search_codebase,
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
            # These are: read_file, scan_codebase, search_codebase
            read_only_ops = {"read_file", "scan_codebase", "search_codebase"}

            # Otherwise, ask for confirmation
            # Bash commands always require confirmation for security
            if tool_type not in read_only_ops:
                while True:
                    description = _format_operation_description(tool_type, parameters)
                    print(f"\n❓ Confirm operation {index}/{total_ops}:")
                    print(f"   {description}")

                    # For write operations, show a preview of the change
                    if tool_type == "write_file":
                        file_path = parameters.get("file_path", "unknown")
                        content = parameters.get("content", "")
                        _show_file_preview_with_diff(file_path, content)

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
                }
            )

    return tool_results


def print_tool_results_summary(tool_results: list[ToolResult]) -> None:
    """Print a summary of the tool results."""
    print("\n🔧 Tool execution results:")
    for tool_result in tool_results:
        tool_type = tool_result["tool_type"]
        result = tool_result["result"]
        print(f"  {tool_type}: {result}")
    print()
