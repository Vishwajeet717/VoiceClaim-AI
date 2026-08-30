from sqlalchemy import text

from database.connection import engine
from rag.embeddings import embed_texts


def ingest_policy_embeddings() -> None:
    """
    Generate Gemini embeddings for policy documents
    that do not already have an embedding and store
    those vectors in Supabase PostgreSQL.
    """

    with engine.begin() as connection:

        rows = connection.execute(
            text(
                """
                SELECT id, content
                FROM policy_documents
                WHERE embedding IS NULL
                ORDER BY id
                """
            )
        ).fetchall()

        if not rows:
            print("No policy documents need embeddings.")
            return

        print(f"Found {len(rows)} policy documents.")

        texts = [row.content for row in rows]

        print("Generating Gemini embeddings...")

        vectors = embed_texts(texts)

        if len(vectors) != len(rows):
            raise RuntimeError(
                "Number of embeddings does not match "
                "number of policy documents."
            )

        print("Saving embeddings to Supabase...")

        for row, vector in zip(rows, vectors):

            connection.execute(
                text(
                    """
                    UPDATE policy_documents
                    SET embedding = CAST(:embedding AS vector)
                    WHERE id = :id
                    """
                ),
                {
                    "id": row.id,
                    "embedding": str(vector),
                },
            )

        print(
            f"Successfully embedded {len(rows)} "
            "policy documents."
        )


if __name__ == "__main__":
    ingest_policy_embeddings()