import sys

from google.genai import Client as GoogleClient

from .actions import handle_async_action
from .context import compact_conversation_history
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
    "# Tone and style\n"
    "You should be concise, direct, and to the point.\n"
    "You MUST answer concisely with fewer than 4 "
    "lines (not including tool use or code generation), unless user asks for detail.\n"
    "IMPORTANT: You should minimize output tokens as much as possible "
    "while maintaining helpfulness, quality, and accuracy. "
    "Only address the specific query or task at hand, "
    "avoiding tangential information unless absolutely critical "
    "for completing the request. If you can answer in 1-3 sentences "
    "or a short paragraph, please do.\n"
    "# Tools and parameters\n"
    "Tools list:\n"
    "- read_file(file_path)\n"
    "- write_file(file_path, content)\n"
    "- delete_file(file_path)\n"
    "- create_directory(dir_path)\n"
    "- execute_bash_command(command)\n"
    "- scan_codebase(root_path)\n"
    "- grep_search(root_path, query, max_results)\n\n"
    "Tool call format:\n"
    "When you need to use a tool, wrap the call in XML like this:\n"
    '<tool_call type="TOOL_NAME">\n'
    '  <parameter name="PARAMETER_NAME">PARAMETER_VALUE</parameter>\n'
    "</tool_call>\n\n"
    "# General guidelines\n"
    "You may include normal text before or after tool calls to explain what "
    "you're doing. Use tools whenever they help, and always be clear and helpful."
)

GOOGLE_AGENT_MODEL = "gemini-flash-latest"

# Approximate token calculation and context compaction settings
# For now we use a test-friendly soft limit. You can increase this later.
MAX_PROMPT_TOKENS_FOR_TESTING = 10_000


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
            if handle_async_action(
                user_input, conversation_history, SYSTEM_PROMPT, MAX_PROMPT_TOKENS_FOR_TESTING
            ):
                continue

        if user_input.lower() in ["quit", "q"]:
            print("\n👋 Goodbye!")
            break

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})

        # Compact conversation history if it grows too large.
        # This ensures we stay within token limits before generating responses.
        compact_conversation_history(
            client=client,
            model=GOOGLE_AGENT_MODEL,
            conversation_history=conversation_history,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=MAX_PROMPT_TOKENS_FOR_TESTING,
        )

        # Build conversation context with system prompt once before the loop.
        # We rely on summarization instead of a fixed sliding window.
        contents = [SYSTEM_PROMPT]
        for msg in conversation_history:
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
                    assistant_message = f"{response_text}\n\nTool results:\n{results_text}"

                conversation_history.append({"role": "assistant", "content": assistant_message})
                # Append to contents for follow-up iterations (avoids rebuilding)
                contents.append(assistant_message)

                # Compact again after adding assistant response to ensure we stay within limits
                compact_conversation_history(
                    client=client,
                    model=GOOGLE_AGENT_MODEL,
                    conversation_history=conversation_history,
                    system_prompt=SYSTEM_PROMPT,
                    max_tokens=MAX_PROMPT_TOKENS_FOR_TESTING,
                )
                # Rebuild contents after compaction
                contents = [SYSTEM_PROMPT]
                for msg in conversation_history:
                    contents.append(msg["content"])

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
