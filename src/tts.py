"""Text-to-speech functionality using ElevenLabs."""

import os

from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

from .utils import Spinner, extract_text_without_tool_calls


def _speak_text(text: str) -> bool:
    """
    Convert text to speech using ElevenLabs TTS and play it.

    This function requires:
    - The elevenlabs package to be installed
    - ELEVENLABS_API_KEY to be set in the environment

    Args:
        text: The text to convert to speech

    Returns:
        True if TTS succeeded, False otherwise
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return False

    # Show loading spinner while preparing TTS
    spinner = Spinner("🐤 pucky is preparing the voice")
    spinner.start()

    try:
        # Initialize the ElevenLabs client
        client = ElevenLabs(api_key=api_key)

        # Convert text to speech
        # Using a default voice - users can customize this later if needed
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="JBFqnCBsd6RMkjVDRZzb",  # Default voice
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
        )

        # Update spinner message when starting to play
        spinner.message = "🐤 pucky is speaking"

        # Play the generated audio
        play(audio)
        spinner.stop()
        return True
    except Exception as e:
        spinner.stop()
        # Print the exception and return False if TTS fails
        print(f"\n❌ TTS failed: {e}\n")
        return False


def speak_latest_response(conversation_history: list[dict[str, str]]) -> None:
    """Speak the latest agent response using text-to-speech."""
    # Find the latest assistant message in conversation history
    for message in reversed(conversation_history):
        if message.get("role") == "assistant":
            content = message.get("content", "")
            if content:
                # Extract text without tool calls for cleaner speech
                text_without_tools = extract_text_without_tool_calls(content)
                if text_without_tools:
                    if _speak_text(text_without_tools):
                        print("\n🔊 Speaking latest response...\n")
                    return

    print("\n⚠️  No agent response found to speak.\n")
