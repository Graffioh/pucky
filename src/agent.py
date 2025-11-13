import sys

from google.genai import Client as GoogleClient

from utils import Spinner, get_user_input, print_response


def run_agent(client: GoogleClient) -> None:
    conversation_history = []

    # Initial greeting
    try:
        # Right now only Google models are supported,
        # may add support for other models later
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=(
                "Hello! Introduce yourself briefly as Pucky, a helpful coding agent."
            ),
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

        # Build conversation context
        contents = []
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
