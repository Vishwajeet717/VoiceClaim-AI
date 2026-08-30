from typing import Any


def evaluate_action(
    action: str,
    state: dict[str, Any],
) -> dict[str, Any]:
    """
    Determine whether a requested insurance action
    is safe for the autonomous agent to perform.
    """

    coverage = state.get("coverage_result") or {}

    injuries = state.get("injuries")
    amount = state.get("amount")

    # ---------------------------------------------------------
    # Read-only actions
    # ---------------------------------------------------------

    if action in {
        "get_customer",
        "get_policy",
        "get_claim_history",
        "check_coverage",
    }:
        return {
            "allowed": True,
            "risk": "LOW",
            "confirmation_required": False,
            "escalation_required": False,
            "reason": "Read-only insurance information retrieval.",
        }

    # ---------------------------------------------------------
    # Draft claim
    # ---------------------------------------------------------

    if action == "create_draft_claim":

        if coverage.get("escalation_required"):
            return {
                "allowed": False,
                "risk": "HIGH",
                "confirmation_required": False,
                "escalation_required": True,
                "reason": (
                    "The coverage assessment requires human review."
                ),
            }

        return {
            "allowed": True,
            "risk": "LOW",
            "confirmation_required": False,
            "escalation_required": False,
            "reason": "Draft claim creation is permitted.",
        }

    # ---------------------------------------------------------
    # Submit claim
    # ---------------------------------------------------------

    if action == "submit_claim":

        if injuries is True:
            return {
                "allowed": False,
                "risk": "HIGH",
                "confirmation_required": False,
                "escalation_required": True,
                "reason": (
                    "Bodily injury claims require human review."
                ),
            }

        if amount is not None and amount > 500000:
            return {
                "allowed": False,
                "risk": "HIGH",
                "confirmation_required": False,
                "escalation_required": True,
                "reason": (
                    "Claims above INR 500000 require manual assessment."
                ),
            }

        if not state.get("customer_confirmation_received"):
            return {
                "allowed": True,
                "risk": "MEDIUM",
                "confirmation_required": True,
                "escalation_required": False,
                "reason": (
                    "Customer confirmation is required before claim submission."
                ),
            }

        return {
            "allowed": True,
            "risk": "MEDIUM",
            "confirmation_required": False,
            "escalation_required": False,
            "reason": (
                "Customer confirmation has been received."
            ),
        }

    # ---------------------------------------------------------
    # Sensitive information
    # ---------------------------------------------------------

    if action == "modify_sensitive_information":
        return {
            "allowed": False,
            "risk": "HIGH",
            "confirmation_required": True,
            "escalation_required": True,
            "reason": (
                "Sensitive customer information requires "
                "additional human verification."
            ),
        }

    # ---------------------------------------------------------
    # Explicit human review
    # ---------------------------------------------------------

    if action in {
        "approve_claim",
        "reject_claim",
        "finalize_coverage_decision",
    }:
        return {
            "allowed": False,
            "risk": "HIGH",
            "confirmation_required": False,
            "escalation_required": True,
            "reason": (
                "Final claims decisions require human review."
            ),
        }

    # ---------------------------------------------------------
    # Unknown action
    # ---------------------------------------------------------

    return {
        "allowed": False,
        "risk": "HIGH",
        "confirmation_required": False,
        "escalation_required": True,
        "reason": "Unknown action is never automatically executable.",
    }