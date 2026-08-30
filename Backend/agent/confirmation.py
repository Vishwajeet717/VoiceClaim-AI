from agent.state import ClaimState


YES_WORDS = {
    "yes",
    "yeah",
    "yep",
    "correct",
    "that's correct",
    "that is correct",
    "looks right",
    "right",
    "confirm",
    "confirmed",
}


NO_WORDS = {
    "no",
    "nope",
    "incorrect",
    "that's wrong",
    "not correct",
    "don't",
    "do not",
}


def classify_confirmation(
    message: str,
) -> str:

    normalized = (
        message
        .strip()
        .lower()
    )

    if normalized in YES_WORDS:
        return "yes"

    if normalized in NO_WORDS:
        return "no"

    return "unclear"


def apply_fact_confirmation(
    state: ClaimState,
    confirmed: bool,
) -> ClaimState:

    if confirmed:
        return {
            **state,
            "fact_confirmation_required": False,
            "fact_confirmation_received": True,
            "next_step": "coverage",
        }

    return {
        **state,
        "fact_confirmation_required": False,
        "fact_confirmation_received": False,
        "next_step": "correction_required",
    }


def apply_submission_confirmation(
    state: ClaimState,
    confirmed: bool,
) -> ClaimState:

    if confirmed:
        return {
            **state,
            "submission_confirmation_required": False,
            "submission_confirmation_received": True,
            "next_step": "submit_claim",
        }

    return {
        **state,
        "submission_confirmation_required": False,
        "submission_confirmation_received": False,
        "next_step": "draft_saved",
    }