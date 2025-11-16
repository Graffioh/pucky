import sys

from google.genai import Client as GoogleClient

from .actions import handle_async_action
from .tools import (
    execute_tool_calls,
    parse_tool_calls,
    print_tool_results_summary,
)
from .utils import (
    Spinner,
    extract_text_without_tool_calls,
    get_user_input,
    print_response,
)

# The modern approcah to include tools is to use structured tools definitions
# but for now I'll keep like this.
SYSTEM_PROMPT = (
    "You are pucky, a helpful coding agent.\n"
    "You can use tools to read/write/delete files, create directories, "
    "run shell commands, and scan or search the codebase.\n\n"
    "Tools and their parameters:\n"
    "- read_file(file_path)\n"
    "- write_file(file_path, content)\n"
    "- delete_file(file_path)\n"
    "- create_directory(dir_path)\n"
    "- execute_bash_command(command)\n"
    "- scan_codebase(root_path)\n"
    "- grep_search(root_path, query, max_results)\n\n"
    "When you need to use a tool, wrap the call in XML like this:\n"
    '<tool_call type="TOOL_NAME">\n'
    '  <parameter name="PARAMETER_NAME">PARAMETER_VALUE</parameter>\n'
    "</tool_call>\n\n"
    "You may include normal text before or after tool calls to explain what "
    "you're doing. Use tools whenever they help, and always be clear and helpful."
)

GOOGLE_AGENT_MODEL = "gemini-flash-latest"


def run_agent(client: GoogleClient) -> None:
    conversation_history = []

    # Initial greeting
    try:
        # Include system prompt in the first message
        initial_message = (
            f"{SYSTEM_PROMPT}\n\n"
            "Hello! Introduce yourself briefly as pucky, "
            "a helpful coding agent and tell the user what you can do."
        )

        # Right now only Google models are supported,
        # may add support for other models later
        response = client.models.generate_content(
            model=GOOGLE_AGENT_MODEL,
            contents=initial_message,
        )

        print_response(response.text)

        # I don't know if it's useful to add the initial greeting
        # to the conversation history
        # conversation_history.append({"role": "assistant", "content": response.text})
    except Exception as e:
        print(f"❌ Error connecting to API: {e}")
        sys.exit(1)

    # Main agent loop
    while True:
        user_input = get_user_input()

        if user_input is None:
            print("\n👋 Goodbye!")
            break

        user_input = user_input.strip()

        if not user_input:
            continue

        if user_input.startswith("@"):
            if handle_async_action(user_input, conversation_history):
                continue

        if user_input.lower() in ["quit", "q"]:
            print("\n👋 Goodbye!")
            break

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})

        # Build conversation context with system prompt once before the loop
        contents = [SYSTEM_PROMPT]
        for msg in conversation_history[-18:]:  # Keep last 18 messages for context
            contents.append(msg["content"])

        # Follow up used later on to execute multiple tool calls in a single response
        follow_up = True
        pending_error = False

        while follow_up:
            follow_up = False

            spinner = None
            try:
                # Show spinner while generating response
                spinner = Spinner("🐤 Pucky is thinking")
                spinner.start()

                # Get response from the model
                response = client.models.generate_content(
                    model=GOOGLE_AGENT_MODEL,
                    contents=contents,
                )

                spinner.stop()
                spinner = None

                response_text = response.text
                if response_text is None:
                    print("\n❌ Error: Received empty response from the model.\n")
                    pending_error = True
                    break

                # Parse tool calls from the response
                tool_calls = parse_tool_calls(response_text)

                # Extract text without tool calls for display
                text_without_tools = extract_text_without_tool_calls(response_text)

                # First, show the assistant's explanation / plan
                if text_without_tools:
                    print_response(text_without_tools)

                tool_results = []
                executed_all_tools = True

                if tool_calls:
                    # Then execute tool calls
                    # (with confirmations handled in execute_tool_calls)
                    tool_results = execute_tool_calls(tool_calls)
                    print_tool_results_summary(tool_results)
                    executed_all_tools = len(tool_results) == len(tool_calls)

                # Add assistant response to history
                # Include tool results in the conversation for context
                assistant_message = response_text
                if tool_results:
                    results_text = "\n".join(
                        [f"{r['tool_type']}: {r['result']}" for r in tool_results]
                    )
                    assistant_message = (
                        f"{response_text}\n\nTool results:\n{results_text}"
                    )

                conversation_history.append(
                    {"role": "assistant", "content": assistant_message}
                )
                # Append to contents for follow-up iterations (avoids rebuilding)
                contents.append(assistant_message)

                # If the assistant used tools and all of them executed,
                # immediately give it another turn (without waiting for user).
                # This is used to execute multiple tool calls in a single response
                if tool_calls and executed_all_tools:
                    follow_up = True
                else:
                    break

            except KeyboardInterrupt:
                if spinner:
                    spinner.stop()
                print("\n\n⚠️  Interrupted. Type your next message or 'q' to quit.")
                pending_error = True
                break
            except Exception as e:
                if spinner:
                    spinner.stop()
                print(f"\n❌ Error: {e}\n")
                pending_error = True
                break

        if pending_error:
            # Remove the failed user message from history so the user can retry
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()
