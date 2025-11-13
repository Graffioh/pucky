import os
import re
import sys
import threading
import time
from pathlib import Path


def load_env_file(env_path: str | Path | None = None) -> None:
    """Load environment variables from a .env file.

    Always looks for .env file in the pucky project directory.
    """
    if env_path is None:
        # Get the directory where utils.py is located (src/)
        utils_dir = Path(__file__).parent

        # Go up to pucky directory (src/ -> pucky/)
        pucky_dir = utils_dir.parent
        env_file = pucky_dir / ".env"
    else:
        env_file = Path(env_path)

    if not env_file.exists():
        return

    with env_file.open() as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            # Parse KEY=VALUE format
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                # Only set if not already in environment
                if key and key not in os.environ:
                    os.environ[key] = value


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
