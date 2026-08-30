import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True,
)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        f"GEMINI_API_KEY is not set. Checked: {ENV_FILE}"
    )


client = genai.Client(
    api_key=GEMINI_API_KEY
)


LIVE_MODEL = "gemini-3.1-flash-live-preview"


LIVE_SYSTEM_INSTRUCTION = """
You are the voice interface for VoiceClaim AI.

The VoiceClaim backend is the authority.

You are responsible only for:
- listening to the caller
- providing speech transcription
- speaking backend-provided responses
- natural voice interaction

You are NOT the insurance decision-maker.

Never independently:
- approve a claim
- reject a claim
- determine coverage
- create a claim
- submit a claim
- modify customer information
- invent policy information
- ask insurance workflow questions on your own

When the backend sends:

[BACKEND_RESPONSE]
...
[/BACKEND_RESPONSE]

speak ONLY the supplied response naturally.

Do not add new insurance information.
Do not alter the meaning.
Do not continue the insurance workflow yourself.

The backend controls the conversation.
"""


async def create_live_session():

    config = {
        "response_modalities": ["AUDIO"],

        "system_instruction": (
            LIVE_SYSTEM_INSTRUCTION
        ),

        "input_audio_transcription": {},

        "output_audio_transcription": {},

        # We control speech boundaries ourselves.
        "realtime_input_config": {
            "automatic_activity_detection": {
                "disabled": True,
            }
        },
    }

    return client.aio.live.connect(
        model=LIVE_MODEL,
        config=config,
    )