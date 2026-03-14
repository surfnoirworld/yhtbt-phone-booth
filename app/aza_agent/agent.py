from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai import types
from pathlib import Path


def load_prompt(filename):
    return (Path(__file__).parent / "prompts" / filename).read_text()


CHARACTER_LAYER = load_prompt("character_layer.txt")
NAVIGATION_LAYER = load_prompt("navigation_layer.txt")
VOICEMAILS = load_prompt("voicemail_transcripts.txt")

FULL_INSTRUCTION = CHARACTER_LAYER + "\n\n" + NAVIGATION_LAYER


root_agent = Agent(
    name="aza_fre",
    model="gemini-2.5-flash-native-audio-preview-12-2025",
    description="Aza Fre, travel agent at Excursion Club in Nearstalgia Bay, searching for Cam through a phone directory",
    instruction=FULL_INSTRUCTION,
    generate_content_config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_budget=256
        )
    ),
)