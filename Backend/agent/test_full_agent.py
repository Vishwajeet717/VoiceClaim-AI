from pprint import pprint

from agent.orchestration import (
    build_conversational_claim_graph,
)


def initial_state():
    return {
        "customer_id": None,
        "customer_phone": "9876543210",
        "customer_verified": False,

        "policy_id": None,
        "policy_number": "POL-10482",

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

        "current_message": None,

        "tool_results": {},
    }


def main():
    graph = build_conversational_claim_graph()

    state = initial_state()

    messages = [
        "My car was hit yesterday around seven in the evening. Nobody was hurt.",
        "Yes, another car was involved.",
    ]

    for message in messages:

        state["current_message"] = message

        state = graph.invoke(state)

        print()
        print("=" * 80)
        print("CUSTOMER")
        print("=" * 80)
        print(message)

        print()
        print("AGENT")
        print("=" * 80)
        print(
            state
            .get("tool_results", {})
            .get("conversation_response")
        )

        print()
        print("NEXT STEP")
        print("=" * 80)
        print(state.get("next_step"))

        print()
        print("STATE")
        print("=" * 80)
        pprint(state)


if __name__ == "__main__":
    main()