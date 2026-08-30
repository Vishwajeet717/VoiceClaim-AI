from datetime import date
from pprint import pprint

from agent.extraction import extract_claim_information


def run_test(title: str, message: str, previous_state=None):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    print()
    print("CUSTOMER:")
    print(message)

    result = extract_claim_information(
        user_message=message,
        previous_state=previous_state,
        reference_date=date(2026, 8, 22),
    )

    print()
    print("EXTRACTED:")
    pprint(result.model_dump())


def main():
    # --------------------------------------------------------------
    # Test 1 — Natural claim statement
    # --------------------------------------------------------------

    run_test(
        "TEST 1 — NORMAL CLAIM",
        (
            "Someone hit my car yesterday around seven in the evening. "
            "Nobody was hurt. There was another vehicle involved and "
            "I think the damage is around eighty-five thousand rupees."
        ),
    )

    # --------------------------------------------------------------
    # Test 2 — Correction
    # --------------------------------------------------------------

    previous_state = {
        "incident_date": "2026-08-20",
        "incident_time": "19:00",
        "claim_type": "motor_collision",
    }

    run_test(
        "TEST 2 — CUSTOMER CORRECTION",
        "Sorry, I just checked. The accident was actually Thursday, not Wednesday.",
        previous_state=previous_state,
    )

    # --------------------------------------------------------------
    # Test 3 — Ambiguity / missing information
    # --------------------------------------------------------------

    run_test(
        "TEST 3 — MISSING INFORMATION",
        "My car was damaged sometime in the evening.",
    )

    # --------------------------------------------------------------
    # Test 4 — Contradiction
    # --------------------------------------------------------------

    previous_state = {
        "incident_date": "2026-08-20",
        "injuries": False,
    }

    run_test(
        "TEST 4 — CONTRADICTION",
        "Actually, someone was injured in the accident.",
        previous_state=previous_state,
    )


if __name__ == "__main__":
    main()