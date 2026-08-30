from typing import Any, TypedDict


class ClaimState(TypedDict, total=False):

    customer_id: int | None
    customer_phone: str | None
    customer_verified: bool

    policy_id: int | None
    policy_number: str | None

    claim_id: int | None
    claim_type: str | None

    incident_date: str | None
    incident_time: str | None
    incident_location: str | None

    description: str | None

    injuries: bool | None
    other_vehicle: bool | None

    amount: float | None

    missing_information: list[str]
    corrections: list[str]
    contradictions: list[str]
    confidence: float

    coverage_result: dict[str, Any] | None
    coverage_status: str | None

    current_intent: str | None
    requested_action: str | None

    action_risk: str | None

    confirmation_required: bool

    fact_confirmation_required: bool
    fact_confirmation_received: bool

    submission_confirmation_required: bool
    submission_confirmation_received: bool

    customer_confirmation_required: bool
    customer_confirmation_received: bool

    escalation_required: bool
    escalation_reason: str | None

    next_step: str | None
    summary: str | None

    submission_status: str | None

    conversation_history: list[dict[str, str]]

    current_message: str | None

    tool_results: dict[str, Any]



def create_initial_claim_state() -> ClaimState:
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

        "fact_confirmation_required": False,
        "fact_confirmation_received": False,

        "submission_confirmation_required": False,
        "submission_confirmation_received": False,

        "customer_confirmation_required": False,
        "customer_confirmation_received": False,

        "escalation_required": False,
        "escalation_reason": None,

        "next_step": "conversation",

        "summary": None,

        "submission_status": None,

        "conversation_history": [],

        "current_message": None,

        "tool_results": {},
    }