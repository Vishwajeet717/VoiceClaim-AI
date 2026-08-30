from typing import Any

from sqlalchemy import text

from database.connection import engine
from rag.embeddings import embed_query


def retrieve_policy_documents(
    question: str,
    policy_id: int | None = None,
    match_threshold: float = 0.0,
    match_count: int = 4,
) -> list[dict[str, Any]]:

    query_vector = embed_query(question)

    query = text(
        """
        SELECT *
        FROM match_policy_documents(
            CAST(:query_embedding AS vector(1536)),
            :match_threshold,
            :match_count,
            :policy_id
        )
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            {
                "query_embedding": str(query_vector),
                "match_threshold": match_threshold,
                "match_count": match_count,
                "policy_id": policy_id,
            },
        ).mappings().all()

    return [dict(row) for row in rows]