from typing import Any

from sqlalchemy import text

from database.connection import engine


def get_customer(phone: str) -> dict[str, Any] | None:
    """
    Look up a customer by phone number.

    Read-only operation.
    """

    if not phone or not phone.strip():
        raise ValueError("Phone number cannot be empty.")

    query = text(
        """
        SELECT
            id,
            name,
            phone,
            email,
            created_at
        FROM customers
        WHERE phone = :phone
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "phone": phone.strip(),
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def get_policy(
    customer_id: int,
    policy_number: str | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve a policy belonging to a customer.

    If policy_number is supplied, retrieve that specific policy.
    Otherwise, retrieve the customer's first policy.
    """

    if policy_number:

        query = text(
            """
            SELECT
                id,
                customer_id,
                policy_number,
                policy_type,
                status,
                start_date,
                end_date,
                coverage_limit,
                created_at
            FROM policies
            WHERE
                customer_id = :customer_id
                AND policy_number = :policy_number
            LIMIT 1
            """
        )

        params = {
            "customer_id": customer_id,
            "policy_number": policy_number.strip(),
        }

    else:

        query = text(
            """
            SELECT
                id,
                customer_id,
                policy_number,
                policy_type,
                status,
                start_date,
                end_date,
                coverage_limit,
                created_at
            FROM policies
            WHERE customer_id = :customer_id
            ORDER BY id
            LIMIT 1
            """
        )

        params = {
            "customer_id": customer_id,
        }

    with engine.connect() as connection:
        row = connection.execute(
            query,
            params,
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def get_claim_history(
    customer_id: int,
    policy_id: int | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve previous claims for a customer.

    Optionally restrict results to a specific policy.
    """

    if policy_id is None:

        query = text(
            """
            SELECT
                id,
                customer_id,
                policy_id,
                incident_date,
                claim_type,
                description,
                amount,
                status,
                created_at
            FROM claims
            WHERE customer_id = :customer_id
            ORDER BY created_at DESC
            """
        )

        params = {
            "customer_id": customer_id,
        }

    else:

        query = text(
            """
            SELECT
                id,
                customer_id,
                policy_id,
                incident_date,
                claim_type,
                description,
                amount,
                status,
                created_at
            FROM claims
            WHERE
                customer_id = :customer_id
                AND policy_id = :policy_id
            ORDER BY created_at DESC
            """
        )

        params = {
            "customer_id": customer_id,
            "policy_id": policy_id,
        }

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            params,
        ).mappings().all()

    return [dict(row) for row in rows]

def create_claim(
    customer_id: int,
    policy_id: int,
    incident_date,
    claim_type: str,
    description: str | None = None,
    amount: float | None = None,
) -> dict[str, Any]:
    """
    Create a claim in draft status.
    """

    query = text(
        """
        INSERT INTO claims (
            customer_id,
            policy_id,
            incident_date,
            claim_type,
            description,
            amount,
            status
        )
        VALUES (
            :customer_id,
            :policy_id,
            :incident_date,
            :claim_type,
            :description,
            :amount,
            'draft'
        )
        RETURNING
            id,
            customer_id,
            policy_id,
            incident_date,
            claim_type,
            description,
            amount,
            status,
            created_at
        """
    )

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "customer_id": customer_id,
                "policy_id": policy_id,
                "incident_date": incident_date,
                "claim_type": claim_type,
                "description": description,
                "amount": amount,
            },
        ).mappings().one()

    return dict(row)


def update_claim(
    claim_id: int,
    **fields: Any,
) -> dict[str, Any] | None:
    """
    Update permitted claim fields.

    The caller must explicitly provide allowed columns.
    """

    allowed_fields = {
        "incident_date",
        "claim_type",
        "description",
        "amount",
        "status",
    }

    updates = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not updates:
        raise ValueError("No valid claim fields supplied.")

    assignments = ", ".join(
        f"{field} = :{field}"
        for field in updates
    )

    query = text(
        f"""
        UPDATE claims
        SET {assignments}
        WHERE id = :claim_id
        RETURNING
            id,
            customer_id,
            policy_id,
            incident_date,
            claim_type,
            description,
            amount,
            status,
            created_at
        """
    )

    params = {
        "claim_id": claim_id,
        **updates,
    }

    with engine.begin() as connection:
        row = connection.execute(
            query,
            params,
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def escalate_claim(
    claim_id: int | None,
    reason: str,
) -> dict[str, Any]:
    """
    Mark a claim for human review.

    This is deliberately simple for the demo.
    """

    if claim_id is None:
        return {
            "success": True,
            "claim_id": None,
            "status": "escalated",
            "reason": reason,
        }

    query = text(
        """
        UPDATE claims
        SET status = 'escalated'
        WHERE id = :claim_id
        RETURNING id, status
        """
    )

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "claim_id": claim_id,
            },
        ).mappings().first()

    if row is None:
        return {
            "success": False,
            "claim_id": claim_id,
            "status": "not_found",
            "reason": reason,
        }

    return {
        "success": True,
        "claim_id": row["id"],
        "status": row["status"],
        "reason": reason,
    }


def submit_claim(
    claim_id: int,
) -> dict[str, Any] | None:
    """
    Submit a draft claim.

    IMPORTANT:
    This function should only be called after the action/risk
    engine has verified that customer confirmation was obtained.
    """

    query = text(
        """
        UPDATE claims
        SET status = 'submitted'
        WHERE
            id = :claim_id
            AND status = 'draft'
        RETURNING
            id,
            customer_id,
            policy_id,
            incident_date,
            claim_type,
            description,
            amount,
            status,
            created_at
        """
    )

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "claim_id": claim_id,
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def get_claim(
    claim_id: int,
) -> dict[str, Any] | None:
    """
    Retrieve a single claim for verification.
    """

    query = text(
        """
        SELECT
            id,
            customer_id,
            policy_id,
            incident_date,
            claim_type,
            description,
            amount,
            status,
            created_at
        FROM claims
        WHERE id = :claim_id
        LIMIT 1
        """
    )

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "claim_id": claim_id,
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(row)