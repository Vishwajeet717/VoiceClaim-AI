from datetime import date

from agent.orchestration import build_claim_graph


def main():
    graph = build_claim_graph()

    initial_state = {
        "customer_phone": "9876543210",
        "customer_verified": False,

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

        "missing_information": [],
        "contradictions": [],

        "confirmation_required": False,
        "escalation_required": False,

        "tool_results": {},
    }

    result = graph.invoke(initial_state)

    print()
    print("=" * 70)
    print("VOICECLAIM AGENT RESULT")
    print("=" * 70)

    for key, value in result.items():
        print()
        print(f"{key}:")
        print(value)


if __name__ == "__main__":
    main()