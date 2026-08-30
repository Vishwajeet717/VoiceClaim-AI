from typing import Any

from langgraph.graph import END, START, StateGraph

from agent.state import ClaimState

from audit.logger import log_action

from insurance.coverage import check_coverage

from insurance.rules import evaluate_action

from agent.confirmation import (
    apply_fact_confirmation,
    apply_submission_confirmation,
    classify_confirmation,
)

from insurance.tools import (
    create_claim,
    escalate_claim,
    get_claim,
    get_claim_history,
    get_customer,
    get_policy,
    submit_claim,
)


def _with_tool_result(
    state: ClaimState,
    key: str,
    value: Any,
) -> dict[str, Any]:
    return {
        **state,
        "tool_results": {
            **state.get("tool_results", {}),
            key: value,
        },
    }


# ============================================================
# CUSTOMER
# ============================================================# ============================================================
# BACKWARD-COMPATIBILITY CONFIRMATION HELPERS
# ============================================================

def apply_customer_confirmation(
    state: ClaimState,
    confirmed: bool,
) -> ClaimState:
    """
    Backward-compatible wrapper for older tests/modules.

    Customer confirmation now refers to the fact-confirmation
    checkpoint before coverage/draft creation.
    """

    return apply_fact_confirmation(
        state,
        confirmed=confirmed,
    )


def apply_claim_submission_confirmation(
    state: ClaimState,
    confirmed: bool,
) -> ClaimState:
    """
    Apply the customer's confirmation to submit the claim.
    """

    return apply_submission_confirmation(
        state,
        confirmed=confirmed,
    )



def identify_customer(
    state: ClaimState,
) -> ClaimState:
    phone = state.get("customer_phone")

    if not phone:
        return {
            **state,
            "missing_information": [
                "customer_phone",
            ],
            "next_step": "request_information",
        }

    customer = get_customer(phone)

    if customer is None:
        return {
            **state,
            "customer_verified": False,
            "escalation_required": True,
            "escalation_reason": (
                "The customer could not be identified "
                "with the provided phone number."
            ),
            "next_step": "escalate",
        }

    updated = _with_tool_result(
        state,
        "customer",
        customer,
    )

    return {
        **updated,
        "customer_id": customer["id"],
        "customer_verified": True,
        "next_step": "get_policy",
    }


# ============================================================
# POLICY
# ============================================================

def retrieve_policy(
    state: ClaimState,
) -> ClaimState:
    customer_id = state.get("customer_id")

    if customer_id is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "Customer identity is unavailable."
            ),
            "next_step": "escalate",
        }

    policy = get_policy(
        customer_id=customer_id,
        policy_number=state.get("policy_number"),
    )

    if policy is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "No matching insurance policy was found."
            ),
            "next_step": "escalate",
        }

    updated = _with_tool_result(
        state,
        "policy",
        policy,
    )

    return {
        **updated,
        "policy_id": policy["id"],
        "policy_number": policy["policy_number"],
        "next_step": "check_history",
    }


# ============================================================
# CLAIM HISTORY
# ============================================================

def retrieve_claim_history(
    state: ClaimState,
) -> ClaimState:
    customer_id = state.get("customer_id")
    policy_id = state.get("policy_id")

    if customer_id is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "Customer identity is unavailable."
            ),
            "next_step": "escalate",
        }

    claims = get_claim_history(
        customer_id=customer_id,
        policy_id=policy_id,
    )

    return _with_tool_result(
        {
            **state,
            "next_step": "check_coverage",
        },
        "claim_history",
        claims,
    )


# ============================================================
# COVERAGE
# ============================================================

def evaluate_coverage(
    state: ClaimState,
) -> ClaimState:
    if not state.get("fact_confirmation_received"):
        return {
            **state,
            "next_step": "fact_confirmation",
        }

    policy = (
        state
        .get("tool_results", {})
        .get("policy")
    )

    if policy is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "Policy information is unavailable."
            ),
            "next_step": "escalate",
        }

    result = check_coverage(
        policy=policy,
        incident_date=state.get("incident_date"),
        claim_type=state.get("claim_type"),
        injuries=state.get("injuries"),
        amount=state.get("amount"),
    )

    updated = {
        **state,
        "coverage_result": result,
        "coverage_status": result.get(
            "coverage_status"
        ),
        "missing_information": result.get(
            "missing_information",
            [],
        ),
    }

    if result.get("escalation_required"):
        updated["escalation_required"] = True
        updated["escalation_reason"] = (
            "; ".join(
                result.get("warnings", [])
            )
            or result.get("reason")
        )
        updated["next_step"] = "escalate"
        return updated

    updated["escalation_required"] = False
    updated["next_step"] = "decide_action"

    return updated


# ============================================================
# ACTION POLICY
# ============================================================

def decide_action(
    state: ClaimState,
) -> ClaimState:
    if state.get("escalation_required"):
        return {
            **state,
            "requested_action": "escalate_claim",
            "action_risk": "HIGH",
            "next_step": "escalate",
        }

    if state.get("missing_information"):
        return {
            **state,
            "requested_action": None,
            "next_step": "request_information",
        }

    decision = evaluate_action(
        action="create_draft_claim",
        state=state,
    )

    if not decision["allowed"]:
        return {
            **state,
            "requested_action": "create_draft_claim",
            "action_risk": decision["risk"],
            "escalation_required": (
                decision["escalation_required"]
            ),
            "escalation_reason": (
                decision["reason"]
            ),
            "next_step": "escalate",
        }

    return {
        **state,
        "requested_action": "create_draft_claim",
        "action_risk": decision["risk"],
        "next_step": "create_draft",
    }


# ============================================================
# DRAFT CREATION
# ============================================================

def create_draft(
    state: ClaimState,
) -> ClaimState:
    decision = evaluate_action(
        action="create_draft_claim",
        state=state,
    )

    if not decision["allowed"]:
        return {
            **state,
            "escalation_required": (
                decision["escalation_required"]
            ),
            "escalation_reason": (
                decision["reason"]
            ),
            "next_step": "escalate",
        }

    customer_id = state.get("customer_id")
    policy_id = state.get("policy_id")

    if customer_id is None or policy_id is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "Customer or policy information is missing."
            ),
            "next_step": "escalate",
        }

    claim = create_claim(
        customer_id=customer_id,
        policy_id=policy_id,
        incident_date=state.get("incident_date"),
        claim_type=state.get("claim_type"),
        description=state.get("description"),
        amount=state.get("amount"),
    )

    log_action(
        action="create_draft_claim",
        status="executed",
        claim_id=claim["id"],
        customer_id=customer_id,
        reason="Draft claim created after customer fact confirmation.",
    )

    claim_reference = (
        f"CLM-{claim['id']:04d}"
    )

    updated = _with_tool_result(
        {
            **state,
            "claim_id": claim["id"],
            "submission_confirmation_required": True,
            "submission_confirmation_received": False,
            "confirmation_required": True,
            "next_step": "submission_confirmation",
        },
        "created_claim",
        claim,
    )

    updated["tool_results"] = {
        **updated.get("tool_results", {}),
        "claim_reference": claim_reference,
    }

    return updated


# ============================================================
# SUBMISSION
# ============================================================

def submit_confirmed_claim(
    state: ClaimState,
) -> ClaimState:
    if not state.get("submission_confirmation_received"):
        return {
            **state,
            "submission_confirmation_required": True,
            "confirmation_required": True,
            "next_step": "submission_confirmation",
        }

    decision = evaluate_action(
        action="submit_claim",
        state=state,
    )

    if not decision["allowed"]:
        log_action(
            action="submit_claim",
            status="blocked",
            claim_id=state.get("claim_id"),
            customer_id=state.get("customer_id"),
            reason=decision["reason"],
        )

        return {
            **state,
            "escalation_required": (
                decision["escalation_required"]
            ),
            "escalation_reason": decision["reason"],
            "next_step": "escalate",
        }

    if decision["confirmation_required"]:
        return {
            **state,
            "submission_confirmation_required": True,
            "confirmation_required": True,
            "next_step": "submission_confirmation",
        }

    claim_id = state.get("claim_id")

    if claim_id is None:
        return {
            **state,
            "escalation_required": True,
            "escalation_reason": (
                "Cannot submit a claim without a claim ID."
            ),
            "next_step": "escalate",
        }

    submitted_claim = submit_claim(
        claim_id=claim_id,
    )

    if submitted_claim is None:
        log_action(
            action="submit_claim",
            status="failed",
            claim_id=claim_id,
            customer_id=state.get("customer_id"),
            reason="Claim submission failed.",
        )

        return {
            **state,
            "submission_status": "failed",
            "next_step": "submission_failed",
        }

    log_action(
        action="submit_claim",
        status="executed",
        claim_id=submitted_claim["id"],
        customer_id=submitted_claim["customer_id"],
        reason=(
            "Claim submitted after explicit "
            "customer confirmation."
        ),
    )

    verified_claim = get_claim(
        claim_id=submitted_claim["id"],
    )

    if (
        verified_claim is None
        or verified_claim["status"] != "submitted"
    ):
        log_action(
            action="verify_claim_submission",
            status="failed",
            claim_id=submitted_claim["id"],
            customer_id=submitted_claim["customer_id"],
            reason="Claim submission could not be verified.",
        )

        return {
            **state,
            "submission_status": "verification_failed",
            "next_step": "submission_failed",
        }

    log_action(
        action="verify_claim_submission",
        status="verified",
        claim_id=verified_claim["id"],
        customer_id=verified_claim["customer_id"],
        reason="Claim status verified as submitted.",
    )

    claim_reference = (
        state
        .get("tool_results", {})
        .get("claim_reference")
    )

    updated = _with_tool_result(
        {
            **state,
            "submission_status": "submitted_and_verified",
            "submission_confirmation_required": False,
            "submission_confirmation_received": True,
            "confirmation_required": False,
            "next_step": "submission_complete",
        },
        "submitted_claim",
        submitted_claim,
    )

    updated["tool_results"] = {
        **updated.get("tool_results", {}),
        "verified_claim": verified_claim,
        "claim_reference": (
            claim_reference
            or f"CLM-{verified_claim['id']:04d}"
        ),
    }

    return updated


# ============================================================
# ESCALATION
# ============================================================

def escalate(
    state: ClaimState,
) -> ClaimState:
    claim_id = state.get("claim_id")
    reason = (
        state.get("escalation_reason")
        or "Claim requires human review."
    )

    # If we already have a claim, mark it escalated.
    # If not, preserve the escalation state for later creation.
    result = escalate_claim(
        claim_id=claim_id,
        reason=reason,
    )

    updated = _with_tool_result(
        {
            **state,
            "escalation_required": True,
            "escalation_reason": reason,
            "next_step": "escalated",
        },
        "escalation",
        result,
    )

    return updated


# ============================================================
# INFORMATION / END NODES
# ============================================================

def request_information(
    state: ClaimState,
) -> ClaimState:
    return {
        **state,
        "next_step": "request_information",
    }


def finalize_draft_state(
    state: ClaimState,
) -> ClaimState:
    return {
        **state,
        "next_step": "submission_confirmation",
        "submission_confirmation_required": True,
        "confirmation_required": True,
    }


def finish(
    state: ClaimState,
) -> ClaimState:
    return {
        **state,
        "next_step": "complete",
    }


# ============================================================
# ROUTING
# ============================================================

def route_after_claim_confirmation(
    state: ClaimState,
) -> str:
    next_step = state.get("next_step")

    if next_step == "coverage":
        return "check_coverage"

    if next_step == "correction_required":
        return "request_information"

    if next_step == "clarify_fact_confirmation":
        return "request_information"

    if next_step == "escalate":
        return "escalate"

    return "check_coverage"


def route_after_coverage(
    state: ClaimState,
) -> str:
    next_step = state.get("next_step")

    if next_step == "escalate":
        return "escalate"

    if next_step == "request_information":
        return "request_information"

    return "decide_action"


def route_after_decision(
    state: ClaimState,
) -> str:
    next_step = state.get("next_step")

    if next_step == "escalate":
        return "escalate"

    if next_step == "request_information":
        return "request_information"

    return "create_draft"


def route_after_draft(
    state: ClaimState,
) -> str:
    if state.get(
        "submission_confirmation_required"
    ):
        return "submission_confirmation"

    return "complete"


def route_after_submission_confirmation(
    state: ClaimState,
) -> str:
    next_step = state.get("next_step")

    if next_step == "submit_claim":
        return "submit_claim"

    if next_step == "draft_saved":
        return "draft_saved"

    if next_step == "clarify_submission_confirmation":
        return "request_information"

    if next_step == "escalate":
        return "escalate"

    return "request_information"


# ============================================================
# GRAPH BUILDER
# ============================================================

def build_claim_graph():
    graph = StateGraph(ClaimState)

    graph.add_node(
        "identify_customer",
        identify_customer,
    )

    graph.add_node(
        "get_policy",
        retrieve_policy,
    )

    graph.add_node(
        "check_history",
        retrieve_claim_history,
    )

    graph.add_node(
        "check_coverage",
        evaluate_coverage,
    )

    graph.add_node(
        "decide_action",
        decide_action,
    )

    graph.add_node(
        "create_draft",
        create_draft,
    )

    graph.add_node(
        "request_information",
        request_information,
    )

    graph.add_node(
        "submission_confirmation",
        lambda state: state,
    )

    graph.add_node(
        "submit_claim",
        submit_confirmed_claim,
    )

    graph.add_node(
        "escalate",
        escalate,
    )

    graph.add_node(
        "complete",
        finish,
    )

    # ---------------------------------------------------------
    # START
    # ---------------------------------------------------------

    graph.add_edge(
        START,
        "identify_customer",
    )

    # ---------------------------------------------------------
    # CUSTOMER
    # ---------------------------------------------------------

    graph.add_edge(
        "identify_customer",
        "get_policy",
    )

    # ---------------------------------------------------------
    # POLICY
    # ---------------------------------------------------------

    graph.add_edge(
        "get_policy",
        "check_history",
    )

    # ---------------------------------------------------------
    # HISTORY
    # ---------------------------------------------------------

    graph.add_edge(
        "check_history",
        "check_coverage",
    )

    # ---------------------------------------------------------
    # COVERAGE
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "check_coverage",
        route_after_coverage,
        {
            "decide_action": "decide_action",
            "request_information": "request_information",
            "escalate": "escalate",
        },
    )

    # ---------------------------------------------------------
    # ACTION
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "decide_action",
        route_after_decision,
        {
            "create_draft": "create_draft",
            "request_information": "request_information",
            "escalate": "escalate",
        },
    )

    # ---------------------------------------------------------
    # DRAFT
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "create_draft",
        route_after_draft,
        {
            "submission_confirmation":
                "submission_confirmation",
            "complete":
                "complete",
        },
    )

    # ---------------------------------------------------------
    # SUBMISSION CONFIRMATION
    #
    # The conversational layer should set:
    # next_step = submit_claim
    # before invoking this branch again.
    # ---------------------------------------------------------

    graph.add_conditional_edges(
        "submission_confirmation",
        route_after_submission_confirmation,
        {
            "submit_claim": "submit_claim",
            "draft_saved": "complete",
            "request_information":
                "request_information",
            "escalate": "escalate",
        },
    )

    # ---------------------------------------------------------
    # SUBMIT
    # ---------------------------------------------------------

    graph.add_edge(
        "submit_claim",
        "complete",
    )

    # ---------------------------------------------------------
    # ESCALATION
    # ---------------------------------------------------------

    graph.add_edge(
        "escalate",
        "complete",
    )

    # ---------------------------------------------------------
    # REQUEST INFORMATION
    # ---------------------------------------------------------

    graph.add_edge(
        "request_information",
        END,
    )

    # ---------------------------------------------------------
    # COMPLETE
    # ---------------------------------------------------------

    graph.add_edge(
        "complete",
        END,
    )

    return graph.compile()


def build_conversational_claim_graph():
    """
    Full state-machine entry point used by the final application.

    The application should first run the conversation manager
    on a customer utterance. When ClaimState says the case is
    ready for insurance processing, this graph can be invoked.

    This separation keeps natural-language handling outside the
    deterministic insurance workflow.
    """

    return build_claim_graph()


def process_claim_workflow(
    state: ClaimState,
) -> ClaimState:
    """
    Convenience function for executing the deterministic
    insurance workflow from the current ClaimState.

    Use this after fact confirmation has been received.
    """

    graph = build_claim_graph()

    return graph.invoke(state)
