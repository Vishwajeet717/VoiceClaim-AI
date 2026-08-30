import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Project structure:
#
# VoiceClaim/
# └── Backend/
#     ├── .env
#     └── rag/
#         └── embeddings.py
#
# parents[0] = rag
# parents[1] = Backend

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


EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 1536


def embed_document(text: str) -> list[float]:
    """
    Generate an embedding for a policy document.

    Documents are embedded as RETRIEVAL_DOCUMENT so that
    they can later be matched against RETRIEVAL_QUERY embeddings.
    """

    if not text or not text.strip():
        raise ValueError("Document text cannot be empty.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no document embedding."
        )

    vector = response.embeddings[0].values

    if vector is None:
        raise RuntimeError(
            "Gemini returned an empty document embedding."
        )

    return list(vector)


def embed_query(text: str) -> list[float]:
    """
    Generate an embedding for a user's search question.

    Queries are embedded as RETRIEVAL_QUERY so they can be
    compared against policy document embeddings.
    """

    if not text or not text.strip():
        raise ValueError("Query text cannot be empty.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=EMBEDDING_DIMENSIONS,
        ),
    )

    if not response.embeddings:
        raise RuntimeError(
            "Gemini returned no query embedding."
        )

    vector = response.embeddings[0].values

    if vector is None:
        raise RuntimeError(
            "Gemini returned an empty query embedding."
        )

    return list(vector)


def embed_text(text: str) -> list[float]:
    """
    Backward-compatible helper.

    Treats arbitrary text as a retrieval query.
    """

    return embed_query(text)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple policy documents.
    """

    if not texts:
        return []

    vectors = []

    for text in texts:
        vectors.append(
            embed_document(text)
        )

    return vectors