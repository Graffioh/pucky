import sys
from dotenv import load_dotenv
from google.genai import Client as GoogleClient
from utils import print_pucky_header

load_dotenv()

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
    print(f"\n🐤 Pucky: {text}\n")


def main():
    print_pucky_header()

    # Create a client (for Gemini Developer API)
    # Make sure to set GOOGLE_API_KEY environment variable (automatically loaded from .env file)
    try:
        google_client = GoogleClient()
    except Exception as e:
        print(f"❌ Error initializing Google client: {e}")
        print("Make sure GOOGLE_API_KEY is set in your .env file")
        sys.exit(1)

    conversation_history = []
    
    # Initial greeting
    try:
        response = google_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Hello! Introduce yourself briefly as Pucky, a helpful coding agent.",
        )
        print_response(response.text)

        # Don't add the initial greeting to the conversation history
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
        
        try:
            # Get response from the model
            response = google_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=contents,
            )
            
            response_text = response.text
            print_response(response_text)
            
            # Add assistant response to history
            conversation_history.append({"role": "assistant", "content": response_text})
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Type your next message or 'q' to quit.")
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            # Remove the failed user message from history
            if conversation_history and conversation_history[-1]["role"] == "user":
                conversation_history.pop()


if __name__ == "__main__":
    main()
