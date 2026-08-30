from typing import Any

from sqlalchemy import text

from database.connection import engine


def log_action(
    action: str,
    status: str,
    claim_id: int | None = None,
    customer_id: int | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Record an agent action in the audit log.
    """

    query = text(
        """
        INSERT INTO audit_logs (
            claim_id,
            customer_id,
            action,
            status,
            reason,
            metadata
        )
        VALUES (
            :claim_id,
            :customer_id,
            :action,
            :status,
            :reason,
            CAST(:metadata AS JSONB)
        )
        RETURNING
            id,
            claim_id,
            customer_id,
            action,
            status,
            reason,
            metadata,
            created_at
        """
    )

    import json

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "claim_id": claim_id,
                "customer_id": customer_id,
                "action": action,
                "status": status,
                "reason": reason,
                "metadata": json.dumps(metadata or {}),
            },
        ).mappings().one()

    return dict(row)