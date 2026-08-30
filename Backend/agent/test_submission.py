from datetime import date

from agent.orchestration import (
    apply_customer_confirmation,
    build_claim_graph,
    submit_confirmed_claim,
)


def main():
    graph = build_claim_graph()

    initial_state = {
        "customer_phone": "9876543210",
        "policy_number": "POL-10482",

        "claim_type": "motor_collision",
        "incident_date": date(2026, 8, 20),
        "incident_time": "19:00",

        "description": (
            "Customer reports accidental vehicle damage "
            "following a collision."
        ),

        "injuries": False,
        "other_vehicle": True,
        "amount": 85000,

        "customer_verified": False,
        "customer_confirmation_required": False,
        "customer_confirmation_received": False,

        "missing_information": [],
        "contradictions": [],

        "confirmation_required": False,
        "escalation_required": False,

        "submission_status": None,
        "tool_results": {},
    }

    print()
    print("=" * 70)
    print("STEP 1 — CREATE DRAFT")
    print("=" * 70)

    draft_result = graph.invoke(initial_state)

    print("Claim ID:", draft_result.get("claim_id"))
    print("Next step:", draft_result.get("next_step"))
    print(
        "Confirmation required:",
        draft_result.get("confirmation_required"),
    )

    print()
    print("=" * 70)
    print("STEP 2 — CUSTOMER CONFIRMS")
    print("=" * 70)

    confirmed_state = apply_customer_confirmation(
        draft_result,
        confirmed=True,
    )

    print(
        "Confirmation received:",
        confirmed_state.get(
            "customer_confirmation_received"
        ),
    )

    print(
        "Next step:",
        confirmed_state.get("next_step"),
    )

    print()
    print("=" * 70)
    print("STEP 3 — SUBMIT")
    print("=" * 70)

    submitted_state = submit_confirmed_claim(
        confirmed_state
    )

    print(
        "Submission status:",
        submitted_state.get("submission_status"),
    )

    print(
        "Claim ID:",
        submitted_state.get("claim_id"),
    )

    verified_claim = (
        submitted_state
        .get("tool_results", {})
        .get("verified_claim")
    )

    print(
        "Verified claim:",
        verified_claim,
    )


if __name__ == "__main__":
    main()