import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.retriever import retrieve_policy_documents


# Load Backend/.env
BACKEND_DIR = Path(__file__).resolve().parent.parent
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


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GEMINI_API_KEY,
)


SYSTEM_PROMPT = """
You are VoiceClaim AI, an insurance claims assistant.

Your job is to explain insurance policy information using
only the policy evidence supplied to you.

STRICT RULES:

1. Never invent insurance coverage.
2. Never invent exclusions.
3. Never invent policy rules.
4. Do not approve or reject an insurance claim.
5. Do not make a final underwriting decision.
6. If the supplied evidence is insufficient, clearly say so.
7. If human review is required, clearly state that.
8. Do not claim that an action was performed unless a backend
   tool actually performed and verified that action.
9. Keep the response concise and suitable for a phone conversation.
"""


def answer_policy_question(
    question: str,
    policy_id: int | None = None,
) -> dict:
    """
    Retrieve relevant policy evidence and generate a
    grounded answer using Gemini.
    """

    documents = retrieve_policy_documents(
        question=question,
        policy_id=policy_id,
        match_count=4,
    )

    if not documents:
        return {
            "answer": (
                "I couldn't find enough relevant information "
                "in the available policy documents to answer "
                "that safely."
            ),
            "sources": [],
        }

    context_parts = []

    for document in documents:
        context_parts.append(
            f"""
Policy Document ID: {document["id"]}
Similarity: {document["similarity"]:.6f}

{document["content"]}
"""
        )

    policy_context = "\n".join(context_parts)

    prompt = f"""
{SYSTEM_PROMPT}

POLICY EVIDENCE:

{policy_context}

CUSTOMER QUESTION:

{question}

Answer the customer's question using ONLY the policy evidence.

Do not mention embeddings, vectors, retrieval, databases,
or internal system details.

If the policy evidence does not provide enough information,
say so clearly.
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": documents,
    }