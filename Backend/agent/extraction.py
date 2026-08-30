import os
from datetime import date
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Environment
# ------------------------------------------------------------------

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


# ------------------------------------------------------------------
# Structured extraction schema
# ------------------------------------------------------------------

ClaimType = Literal[
    "motor_collision",
    "motor_damage",
    "theft",
    "fire",
    "unknown",
]


class ClaimExtraction(BaseModel):
    """
    Facts extracted from the customer's conversation.

    This model describes what the customer said.
    It does not make a coverage or claims decision.
    """

    customer_phone: str | None = Field(
        default=None,
        description="Phone number explicitly provided by the customer."
    )

    policy_number: str | None = Field(
        default=None,
        description="Insurance policy number explicitly provided by the customer."
    )

    claim_type: ClaimType | None = Field(
        default=None,
        description="Type of insurance event described by the customer."
    )

    incident_date: str | None = Field(
        default=None,
        description="Incident date in YYYY-MM-DD format."
    )

    incident_time: str | None = Field(
        default=None,
        description="Approximate incident time in HH:MM 24-hour format when known."
    )

    incident_location: str | None = Field(
        default=None,
        description="Location of the incident if provided."
    )

    injuries: bool | None = Field(
        default=None,
        description="Whether anyone was injured, if the customer states this."
    )

    other_vehicle: bool | None = Field(
        default=None,
        description="Whether another vehicle was involved."
    )

    amount: float | None = Field(
        default=None,
        description="Estimated claim or damage amount if stated."
    )

    description: str | None = Field(
        default=None,
        description="Concise description of the incident."
    )

    corrections: list[str] = Field(
        default_factory=list,
        description="Corrections the customer made to information previously stated."
    )

    contradictions: list[str] = Field(
        default_factory=list,
        description="Conflicts between the current message and previously stored state."
    )

    missing_information: list[str] = Field(
        default_factory=list,
        description="Important claim information that is still missing based on the conversation so far."
    )

    confidence: float = Field(
        default=1.0,
        description="Overall extraction confidence from 0.0 to 1.0."
    )


# ------------------------------------------------------------------
# Extraction prompt
# ------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = """
You are the structured information extraction component of VoiceClaim AI.

Your job is ONLY to extract facts from an insurance customer's conversation.

You are NOT allowed to:
- decide whether a claim is covered
- approve a claim
- reject a claim
- decide whether an action is permitted
- invent facts
- invent dates
- invent policy information

Extract only information supported by the conversation.

IMPORTANT DATE RULES:
- The reference date supplied by the application is authoritative.
- Convert relative dates such as "today", "yesterday", and "last Thursday"
  into actual YYYY-MM-DD dates when the meaning is sufficiently clear.
- Never return words such as "yesterday" as incident_date.
- If a date cannot be resolved reliably, return null.

IMPORTANT CORRECTION RULES:
- If the customer corrects earlier information, use the corrected value.
- Record the correction in `corrections`.
- If the current message conflicts with previous state and the customer
  has NOT clearly corrected the earlier value, record the conflict in
  `contradictions` instead of silently choosing one.

IMPORTANT UNKNOWN INFORMATION RULE:
- Use null when information is unknown.
- Do not guess.
- Use claim_type="unknown" when the incident cannot be classified safely.

The extraction should be suitable for a downstream insurance agent.
"""


def extract_claim_information(
    user_message: str,
    previous_state: dict | None = None,
    reference_date: date | None = None,
) -> ClaimExtraction:
    """
    Extract structured claim facts from the latest customer message.

    previous_state allows the extractor to detect corrections and
    contradictions across conversation turns.
    """

    if not user_message or not user_message.strip():
        raise ValueError("user_message cannot be empty.")

    if reference_date is None:
        reference_date = date.today()

    previous_state = previous_state or {}

    prompt = f"""
{SYSTEM_INSTRUCTIONS}

REFERENCE DATE:
{reference_date.isoformat()}

PREVIOUS CLAIM STATE:
{previous_state}

LATEST CUSTOMER MESSAGE:
{user_message}

Return structured data for the latest message.

When updating existing information:
- Preserve previous values unless the customer clearly changes them.
- Report explicit corrections.
- Report unresolved contradictions.
- Do not make insurance decisions.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ClaimExtraction,
            temperature=0,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned no structured extraction."
        )

    try:
        return ClaimExtraction.model_validate_json(
            response.text
        )
    except Exception as exc:
        raise RuntimeError(
            "Gemini returned invalid structured extraction."
        ) from exc