import re
import sys
import threading
import time
from typing import Any


def print_pucky_header():
    """Print the pucky ASCII art header."""
    pucky_ascii_header = r"""
             _       _ |     
            |_) |_| (_ |< \/ 
            |             /  
                   -                       
                 :=+-                    
               +:...:=++=====            
            %*-.           ..:+=         
         **=:.                  :==      
       **--:.                     ==     
      #++-:                        -+    
     *===-:.                       .=    
**+  =---::.                  ......-.   
  .+=--::-:.     ..:=++=.   .       .=   
    .:*-:-:.:+=::.                   .=  
       .:--..                          :=
-..    ...::.                    ....:::=
#==:.   .:-.:.         ..-+*++-::...   .=
  %#*+:::::::.   .-=-..              .-= 
      +:--:-:::. .                 .-+   
       *----=-==...              -+-     
        *#*====--:::.          :+        
            #**==--:.            -+      
             *+=---..             :+     
            %+=---:                :+    
            +=-:::..                :*   
           =:-:.:-:.                 -*                 
"""
    print(pucky_ascii_header)
    print("Type 'quit' or 'q' to end the conversation\n")


def get_user_input(prompt="You: "):
    """Get input from the user, handling multi-line input."""
    lines = []
    try:
        while True:
            line = input(prompt if not lines else "... ")
            if not line.strip() and lines:
                break
            lines.append(line)
            if line.strip() and not line.endswith("\\"):
                break
    except (EOFError, KeyboardInterrupt):
        return None
    return "\n".join(lines).strip()


def print_response(text):
    """Print the agent's response with nice formatting."""
    print(f"\n🐤 pucky: {text}\n")


def parse_tool_calls(text: str) -> list[dict[str, Any]]:
    """
    Parse XML tool calls from agent response text.

    Args:
        text: The response text that may contain XML tool calls

    Returns:
        A list of dictionaries, each containing:
        - 'type': The tool type (e.g., 'read_file', 'write_file')
        - 'parameters': A dict of parameter name-value pairs
        - 'raw_xml': The raw XML string for this tool call

    Example:
        >>> text = ('I will read the file. <tool_call type="read_file">\\n'
        ...         '<parameter name="file_path">src/main.py</parameter>\\n'
        ...         '</tool_call>')
        >>> parse_tool_calls(text)
        [{'type': 'read_file', 'parameters': {'file_path': 'src/main.py'},
        ...  'raw_xml': '...'}]
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
                "type": tool_type,
                "parameters": parameters,
                "raw_xml": raw_xml,
            }
        )

    return tool_calls


def extract_text_without_tool_calls(text: str) -> str:
    """
    Extract text content from response, removing all tool call XML blocks.

    Args:
        text: The response text that may contain XML tool calls

    Returns:
        The text with all tool call XML blocks removed
    """
    # Remove all tool_call blocks
    pattern = r"<tool_call\s+type=\"[^\"]+\">.*?</tool_call>"
    cleaned_text = re.sub(pattern, "", text, flags=re.DOTALL)

    # Clean up extra whitespace
    cleaned_text = re.sub(r"\n\s*\n\s*\n", "\n\n", cleaned_text)
    return cleaned_text.strip()


class Spinner:
    """A simple ASCII spinner for loading indicators."""

    def __init__(self, message="🐤 pucky is thinking"):
        self.message = message
        self.spinner_chars = "|/-\\"
        self.stop_spinner = False
        self.spinner_thread = None

    def _spin(self):
        """Internal method that runs the spinner animation."""
        i = 0
        while not self.stop_spinner:
            char = self.spinner_chars[i % len(self.spinner_chars)]
            sys.stdout.write(f"\r{self.message} {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        """Start the spinner in a separate thread."""
        self.stop_spinner = False
        self.spinner_thread = threading.Thread(target=self._spin, daemon=True)
        self.spinner_thread.start()

    def stop(self):
        """Stop the spinner and clear the line."""
        self.stop_spinner = True
        if self.spinner_thread:
            self.spinner_thread.join(timeout=0.2)
        sys.stdout.write("\r" + " " * (len(self.message) + 3) + "\r")
        sys.stdout.flush()
