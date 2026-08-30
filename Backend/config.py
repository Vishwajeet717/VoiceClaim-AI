import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent
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


GEMINI_EXTRACTION_MODEL = "gemini-3.5-flash-lite"
GEMINI_CONVERSATION_MODEL = "gemini-3.5-flash-lite"
GEMINI_RAG_MODEL = "gemini-3.5-flash"
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

EMBEDDING_DIMENSIONS = 1536