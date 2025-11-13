"""File operation tools for the code agent."""

import re
from pathlib import Path
from typing import TypedDict


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
    """Read a file and return its contents."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is not a file."
        return path.read_text()
    except Exception as e:
        return f"Error reading file: {str(e)}"


def _write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return f"Successfully wrote to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {str(e)}"


def _delete_file(file_path: str) -> str:
    """Delete a file."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"Error: File '{file_path}' does not exist."
        if not path.is_file():
            return f"Error: '{file_path}' is not a file."
        path.unlink()
        return f"Successfully deleted '{file_path}'"
    except Exception as e:
        return f"Error deleting file: {str(e)}"


def _create_directory(dir_path: str) -> str:
    """Create a directory (and parent directories if needed)."""
    try:
        path = Path(dir_path)
        if path.exists():
            if path.is_dir():
                return f"Directory '{dir_path}' already exists."
            else:
                return f"Error: '{dir_path}' exists but is not a directory."
        path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created directory '{dir_path}'"
    except Exception as e:
        return f"Error creating directory: {str(e)}"


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
        }

        # Print operations that will be performed
        print("\n🔧 Operations to perform:")
        for tool_call in tool_calls:
            tool_type = tool_call["call_type"]
            parameters = tool_call["parameters"]

            # Format operation description
            if tool_type == "read_file":
                file_path = parameters.get("file_path", "unknown")
                print(f"  📖 Reading file: {file_path}")
            elif tool_type == "write_file":
                file_path = parameters.get("file_path", "unknown")
                print(f"  ✏️  Writing into file: {file_path}")
            elif tool_type == "delete_file":
                file_path = parameters.get("file_path", "unknown")
                print(f"  🗑️  Deleting file: {file_path}")
            elif tool_type == "create_directory":
                dir_path = parameters.get("dir_path", "unknown")
                print(f"  📁 Creating directory: {dir_path}")
            else:
                print(f"  ❓ Unknown operation: {tool_type}")
        print()

        for tool_call in tool_calls:
            tool_type = tool_call["call_type"]
            parameters = tool_call["parameters"]

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
