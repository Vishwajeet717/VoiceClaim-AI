from datetime import date

from agent.confirmation import (
    apply_fact_confirmation,
    apply_submission_confirmation,
    classify_confirmation,
)
from agent.conversation import merge_extraction_into_state
from agent.extraction import extract_claim_information
from agent.intents import classify_conversation_intent
from agent.questioning import (
    generate_next_question,
    get_missing_fields,
)
from agent.state import ClaimState
from agent.summary import build_claim_summary


def _append_history(
    state: ClaimState,
    role: str,
    message: str,
) -> list[dict[str, str]]:
    history = state.get(
        "conversation_history",
        [],
    )

    return [
        *history,
        {
            "role": role,
            "message": message,
        },
    ]


def _clear_confirmation_flags(
    state: ClaimState,
) -> ClaimState:
    return {
        **state,
        "confirmation_required": False,
        "fact_confirmation_required": False,
        "submission_confirmation_required": False,
    }


def _is_claim_context(
    state: ClaimState,
) -> bool:
    """
    Returns True when the customer is already inside
    an insurance workflow.

    This allows short answers such as:
        9876543210
        Thursday
        around seven
        no
        yes

    to be treated as claim information.

    IMPORTANT:
    Explicit social/joke intents are handled BEFORE this
    function is used.
    """

    return (
        state.get("current_intent")
        in {
            "insurance_claim",
            "file_claim",
        }
        or state.get("next_step")
        in {
            "request_information",
            "resolve_contradiction",
            "correction_required",
            "fact_confirmation",
            "clarify_fact_confirmation",
            "submission_confirmation",
            "clarify_submission_confirmation",
        }
        or bool(
            state.get(
                "missing_information",
                [],
            )
        )
    )


def _remember_resume_step(
    state: ClaimState,
) -> ClaimState:
    """
    Remember where the insurance conversation should resume
    after a social/joke interruption.
    """

    next_step = state.get("next_step")

    if next_step in {
        "request_information",
        "resolve_contradiction",
        "fact_confirmation",
        "submission_confirmation",
    }:
        return {
            **state,
            "tool_results": {
                **state.get(
                    "tool_results",
                    {},
                ),
                "resume_next_step": next_step,
            },
        }

    return state


def _resume_after_social(
    state: ClaimState,
) -> ClaimState:
    resume_step = (
        state
        .get("tool_results", {})
        .get("resume_next_step")
    )

    if resume_step:
        return {
            **state,
            "next_step": resume_step,
        }

    return state


def process_customer_message(
    state: ClaimState,
    message: str,
    reference_date: date | None = None,
) -> ClaimState:
    """
    Process one customer utterance.

    Priority:

    1. Confirmation gates
    2. Explicit social / joke intent
    3. Claim-context answers
    4. New insurance intent
    5. Unrelated conversation
    """

    if reference_date is None:
        reference_date = date.today()

    message = (message or "").strip()

    if not message:
        return {
            **state,
            "next_step": "conversation",
        }

    updated: ClaimState = {
        **state,
        "current_message": message,
        "conversation_history": _append_history(
            state,
            "customer",
            message,
        ),
    }

    # =========================================================
    # 1. FACT CONFIRMATION
    # =========================================================

    if updated.get(
        "fact_confirmation_required"
    ):
        result = classify_confirmation(
            message
        )

        if result == "yes":
            return apply_fact_confirmation(
                updated,
                confirmed=True,
            )

        if result == "no":
            return apply_fact_confirmation(
                updated,
                confirmed=False,
            )

        return {
            **updated,
            "next_step": "clarify_fact_confirmation",
        }

    # =========================================================
    # 2. SUBMISSION CONFIRMATION
    # =========================================================

    if updated.get(
        "submission_confirmation_required"
    ):
        result = classify_confirmation(
            message
        )

        if result == "yes":
            return apply_submission_confirmation(
                updated,
                confirmed=True,
            )

        if result == "no":
            return apply_submission_confirmation(
                updated,
                confirmed=False,
            )

        return {
            **updated,
            "next_step": "clarify_submission_confirmation",
        }

    # =========================================================
    # 3. CORRECTION AFTER FACT CONFIRMATION "NO"
    # =========================================================

    if updated.get(
        "next_step"
    ) == "correction_required":
        updated = _clear_confirmation_flags(
            updated
        )

    # =========================================================
    # 4. ALWAYS CLASSIFY THE CURRENT MESSAGE FIRST
    #
    # This fixes:
    # "tell me a joke"
    # "hello"
    # "thanks"
    #
    # even while a claim conversation is active.
    # =========================================================

    intent = classify_conversation_intent(
        message
    )

    # =========================================================
    # 5. EXPLICIT SOCIAL / JOKE HANDLING
    # =========================================================

    if intent in {
        "greeting",
        "thanks",
        "goodbye",
        "joke",
        "joke_reaction",
    }:

        # Remember where the insurance conversation was.
        updated = _remember_resume_step(
            updated
        )

        updated["current_intent"] = intent

        if intent == "greeting":
            updated["next_step"] = "greeting"

        elif intent == "thanks":
            updated["next_step"] = "thanks"

        elif intent == "goodbye":
            updated["next_step"] = "goodbye"

        elif intent == "joke":
            updated["next_step"] = "joke"

        elif intent == "joke_reaction":
            updated["next_step"] = "joke_reaction"

        return updated

    # =========================================================
    # 6. DETERMINE WHETHER WE ARE IN CLAIM CONTEXT
    # =========================================================

    claim_context = _is_claim_context(
        updated
    )

    # =========================================================
    # 7. UNRELATED ONLY APPLIES WHEN WE ARE NOT WAITING
    # FOR A CLAIM ANSWER
    # =========================================================

    if intent == "unrelated" and not claim_context:

        updated["current_intent"] = "unrelated"
        updated["next_step"] = "unrelated"

        return updated

    # =========================================================
    # 8. INSURANCE CONTEXT
    #
    # Either:
    # - explicit insurance intent
    # - OR we're already inside the claim flow
    # =========================================================

    if (
        intent == "insurance_claim"
        or claim_context
    ):
        updated["current_intent"] = (
            "insurance_claim"
        )

    else:
        updated["current_intent"] = (
            "insurance_claim"
        )

    # =========================================================
    # 9. INSURANCE EXTRACTION
    # =========================================================

    extraction = extract_claim_information(
        user_message=message,
        previous_state=dict(updated),
        reference_date=reference_date,
    )

    updated = merge_extraction_into_state(
        state=updated,
        extraction=extraction,
    )

    # =========================================================
    # 10. CONTRADICTIONS
    # =========================================================

    contradictions = updated.get(
        "contradictions",
        [],
    )

    if contradictions:

        updated["next_step"] = (
            "resolve_contradiction"
        )

        updated["escalation_required"] = False

        return updated

    # =========================================================
    # 11. MISSING INFORMATION
    # =========================================================

    missing_fields = get_missing_fields(
        updated
    )

    updated["missing_information"] = (
        missing_fields
    )

    if missing_fields:

        updated["next_step"] = (
            "request_information"
        )

        return updated

    # =========================================================
    # 12. ALL FACTS COLLECTED
    # =========================================================

    summary = build_claim_summary(
        updated
    )

    updated["summary"] = summary

    updated["fact_confirmation_required"] = True
    updated["fact_confirmation_received"] = False
    updated["confirmation_required"] = True

    updated["next_step"] = (
        "fact_confirmation"
    )

    return updated


def get_next_conversation_response(
    state: ClaimState,
) -> str:
    """
    Convert ClaimState into a customer-facing response.
    """

    next_step = state.get(
        "next_step"
    )

    # =========================================================
    # GENERAL CONVERSATION
    # =========================================================

    if next_step == "greeting":
        return (
            "Hello! I'm doing well, thank you. "
            "I'm here to help you with your insurance claim. "
            "What can I help you with today?"
        )

    if next_step == "thanks":
        response = (
            "You're very welcome. "
            "Let me know what you'd like help with."
        )

        return response

    if next_step == "goodbye":
        return (
            "You're welcome. "
            "Thank you for calling VoiceClaim."
        )

    # =========================================================
    # JOKE
    # =========================================================

    if next_step == "joke":
        return (
            "You crashed you vehicle? "
            "Seems like your wife asked you to stay in touch with your feminine side."
            
        )

    if next_step == "joke_reaction":
        return (
            "Yes. And so is your vehicle. Hahaha."
        )

    # =========================================================
    # UNRELATED
    # =========================================================

    if next_step == "unrelated":
        return (
            "I'm here specifically to help with insurance "
            "and claims. What can I help you with regarding "
            "your policy or claim?"
        )

    # =========================================================
    # CONTRADICTION
    # =========================================================

    if next_step == "resolve_contradiction":

        contradictions = state.get(
            "contradictions",
            [],
        )

        if contradictions:
            return (
                "I want to make sure I have this right. "
                f"{contradictions[0]} "
                "Which information should I use?"
            )

        return (
            "I found conflicting information. "
            "Could you clarify the correct details?"
        )

    # =========================================================
    # MISSING INFORMATION
    # =========================================================

    if next_step == "request_information":
        return generate_next_question(
            state
        )

    # =========================================================
    # FACT CONFIRMATION
    # =========================================================

    if next_step == "fact_confirmation":

        return state.get(
            "summary",
            "Please confirm that the claim information is correct.",
        )

    if next_step == "clarify_fact_confirmation":

        return (
            "Please say yes if the claim summary is correct, "
            "or tell me what needs to be changed."
        )

    if next_step == "correction_required":

        return (
            "No problem. Tell me which part of the claim "
            "information needs to be corrected."
        )

    # =========================================================
    # COVERAGE
    # =========================================================

    if next_step in {
        "coverage",
        "ready_for_coverage",
    }:
        return (
            "Thanks. I'll check the claim against "
            "your policy now."
        )

    # =========================================================
    # SUBMISSION
    # =========================================================

    if next_step == "submission_confirmation":

        return (
            "Your claim draft is ready. "
            "Would you like me to submit it now?"
        )

    if next_step == "clarify_submission_confirmation":

        return (
            "Please say yes if you'd like me to submit "
            "the claim, or no if you'd prefer to leave "
            "it as a draft."
        )

    if next_step == "draft_saved":

        return (
            "I've saved the claim as a draft. "
            "It has not been submitted."
        )

    if next_step == "submission_complete":

        reference = (
            state
            .get("tool_results", {})
            .get("claim_reference")
        )

        if reference:
            return (
                "Your claim has been submitted successfully. "
                f"Your claim reference is {reference}."
            )

        return (
            "Your claim has been submitted successfully."
        )

    if next_step == "submission_failed":

        return (
            "I wasn't able to complete the claim submission. "
            "I don't want to mislead you, so this needs review."
        )

    # =========================================================
    # ESCALATION
    # =========================================================

    if next_step in {
        "escalate",
        "escalated",
    }:

        reason = state.get(
            "escalation_reason"
        )

        if reason:
            return (
                "This claim requires human review. "
                f"{reason}"
            )

        return (
            "This claim requires review by a human "
            "claims specialist. I won't submit it automatically."
        )

    # =========================================================
    # FALLBACK
    # =========================================================

    return (
        "I'm here to help with your insurance needs. "
        "What would you like to do?"
    )