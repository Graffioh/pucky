import sys

from google.genai import Client as GoogleClient

from utils import Spinner, get_user_input, print_response

SYSTEM_PROMPT = (
    "You are Pucky, a helpful coding agent. "
    "When you need to use tools to help the user, "
    "you must wrap your tool calls in XML tags.\n\n"
    "AVAILABLE TOOLS:\n"
    "- read_file: Read the contents of a file\n"
    "- write_file: Write content to a file\n"
    "- delete_file: Delete a file\n"
    "- create_directory: Create a directory\n\n"
    "TOOL CALL FORMAT:\n"
    "When you need to use a tool, wrap it in XML tags like this:\n\n"
    '<tool_call type="TOOL_NAME">\n'
    '<parameter name="PARAMETER_NAME">PARAMETER_VALUE</parameter>\n'
    '<parameter name="PARAMETER_NAME2">PARAMETER_VALUE2</parameter>\n'
    "</tool_call>\n\n"
    " "
    "EXAMPLES:\n\n"
    "To read a file:\n"
    '<tool_call type="read_file">\n'
    '<parameter name="file_path">src/main.py</parameter>\n'
    "</tool_call>\n\n"
    "To write a file:\n"
    '<tool_call type="write_file">\n'
    '<parameter name="file_path">example.txt</parameter>\n'
    '<parameter name="content">Hello, world!</parameter>\n'
    "</tool_call>\n\n"
    "To delete a file:\n"
    '<tool_call type="delete_file">\n'
    '<parameter name="file_path">temp.txt</parameter>\n'
    "</tool_call>\n\n"
    "To create a directory:\n"
    '<tool_call type="create_directory">\n'
    '<parameter name="dir_path">new_folder</parameter>\n'
    "</tool_call>\n\n"
    " "
    "IMPORTANT RULES:\n"
    "1. Always use XML tags when you need to call a tool\n"
    "2. You can include regular text before or after tool calls "
    "to explain what you're doing\n"
    "3. You can make multiple tool calls in a single response if needed\n"
    "4. If you don't need to use any tools, respond normally "
    "without XML tags\n"
    "5. Always be helpful, clear, and explain your actions to the user"
)


def run_agent(client: GoogleClient) -> None:
    conversation_history = []

    # Initial greeting
    try:
        # Right now only Google models are supported,
        # may add support for other models later
        # Include system prompt in the first message
        initial_message = (
            f"{SYSTEM_PROMPT}\n\n"
            "Hello! Introduce yourself briefly as pucky, "
            "a helpful coding agent and tell the user what you can do."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
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

        if user_input.lower() in ["quit", "q"]:
            print("\n👋 Goodbye!")
            break

        if not user_input:
            continue

        # Add user message to history
        conversation_history.append({"role": "user", "content": user_input})

        # Build conversation context with system prompt
        contents = [SYSTEM_PROMPT]
        for msg in conversation_history[-10:]:  # Keep last 10 messages for context
            contents.append(msg["content"])

        spinner = None
        try:
            # Show spinner while generating response
            spinner = Spinner("🐤 Pucky is thinking")
            spinner.start()

            # Get response from the model
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=contents,
            )

            spinner.stop()
            spinner = None

            response_text = response.text
            print_response(response_text)

            # TODO: Implement tool calling

            # Add assistant response to history
            conversation_history.append({"role": "assistant", "content": response_text})

        except KeyboardInterrupt:
            if spinner:
                spinner.stop()
            print("\n\n⚠️  Interrupted. Type your next message or 'q' to quit.")
        except Exception as e:
            if spinner:
                spinner.stop()
            print(f"\n❌ Error: {e}\n")
            # Remove the failed user message from history
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()
