from datetime import date
from pprint import pprint

from agent.conversation_manager import (
    get_next_conversation_response,
    process_customer_message,
)


def create_initial_state():
    return {
        "customer_id": None,
        "customer_phone": None,
        "customer_verified": False,

        "policy_id": None,
        "policy_number": None,

        "claim_id": None,
        "claim_type": None,

        "incident_date": None,
        "incident_time": None,
        "incident_location": None,

        "description": None,

        "injuries": None,
        "other_vehicle": None,

        "amount": None,

        "missing_information": [],
        "corrections": [],
        "contradictions": [],

        "confidence": 1.0,

        "coverage_result": None,
        "coverage_status": None,

        "current_intent": "file_claim",
        "requested_action": None,

        "action_risk": None,
        "confirmation_required": False,

        "customer_confirmation_required": False,
        "customer_confirmation_received": False,

        "escalation_required": False,
        "escalation_reason": None,

        "next_step": None,

        "summary": None,

        "submission_status": None,

        "tool_results": {},
    }


def show_turn(
    turn_number: int,
    customer_message: str,
    state: dict,
):
    print()
    print("=" * 80)
    print(f"TURN {turn_number}")
    print("=" * 80)

    print()
    print("CUSTOMER:")
    print(customer_message)

    print()
    print("NEXT AGENT RESPONSE:")
    print(get_next_conversation_response(state))

    print()
    print("STATE:")
    pprint(state)


def main():

    state = create_initial_state()

    conversation = [
        (
            "My car was hit yesterday around seven in "
            "the evening. Nobody was hurt."
        ),
        (
            "Yes, another car was involved."
        ),
        (
            "I think the damage is around eighty-five "
            "thousand rupees."
        ),
        (
            "The accident happened on Thursday, not yesterday. "
            "I checked my calendar."
        ),
    ]

    for index, message in enumerate(
        conversation,
        start=1,
    ):

        state = process_customer_message(
            state=state,
            message=message,
            reference_date=date(2026, 8, 22),
        )

        show_turn(
            turn_number=index,
            customer_message=message,
            state=state,
        )


if __name__ == "__main__":
    main()