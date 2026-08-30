import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.state import ClaimState


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

MODEL = "gemini-3.5-flash-lite"


REQUIRED_FIELDS = [
    "customer_phone",
    "incident_date",
    "incident_time",
    "claim_type",
    "injuries",
    "other_vehicle",
    "description",
]


def get_missing_fields(
    state: ClaimState,
) -> list[str]:
    """
    Determine which claim fields are still required
    before the agent can proceed to coverage evaluation.
    """

    missing: list[str] = []

    for field in REQUIRED_FIELDS:
        value = state.get(field)

        if value is None:
            missing.append(field)

        elif isinstance(value, str) and not value.strip():
            missing.append(field)

    return missing


def get_question_priority(
    missing_fields: list[str],
) -> list[str]:

    priority = [
        "customer_phone",
        "incident_date",
        "incident_time",
        "claim_type",
        "injuries",
        "other_vehicle",
        "description",
    ]

    return [
        field
        for field in priority
        if field in missing_fields
    ]


def generate_next_question(
    state: ClaimState,
) -> str:
    """
    Generate a natural phone-style question for the most
    important missing claim field.

    The LLM only phrases the question.
    It does not decide insurance rules.
    """

    missing_fields = get_missing_fields(state)

    if not missing_fields:
        return ""

    ordered_fields = get_question_priority(
        missing_fields
    )

    next_field = ordered_fields[0]

    question_instructions = {
        "incident_date": (
            "Ask when the incident happened. "
            "If the customer already gave an approximate date, "
            "ask for clarification rather than repeating the same question."
        ),
        "incident_time": (
            "Ask approximately what time the incident happened. "
            "A rough time is acceptable."
        ),
        "claim_type": (
            "Ask what happened to the vehicle and determine the "
            "nature of the incident from the customer's answer."
        ),
        "injuries": (
            "Ask whether anyone was injured in the incident."
        ),
        "other_vehicle": (
            "Ask whether another vehicle was involved."
        ),
        "description": (
            "Ask the customer to briefly describe what happened."
        ),
        "customer_phone": (
        "Ask the customer to confirm the phone number associated "
        "with their insurance policy."
        ),
    }

    instruction = question_instructions[next_field]

    prompt = f"""
You are the conversational question generator for VoiceClaim AI.

The customer is speaking with an insurance claims agent.

Your job is ONLY to phrase the next question naturally.

Do not:
- make coverage decisions
- mention internal systems
- mention missing fields
- ask multiple questions at once
- invent information

The next information we need is:

{instruction}

CURRENT CLAIM STATE:

{dict(state)}

Return exactly one short question suitable for a phone call.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned no question."
        )

    return response.text.strip()