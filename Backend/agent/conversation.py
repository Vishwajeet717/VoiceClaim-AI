from agent.extraction import ClaimExtraction
from agent.state import ClaimState


def merge_extraction_into_state(
    state: ClaimState,
    extraction: ClaimExtraction,
) -> ClaimState:
    """
    Merge newly extracted facts into the current ClaimState.
    """

    updated: ClaimState = {
        **state,
    }

    extraction_data = extraction.model_dump(
        exclude_none=True
    )

    direct_fields = {
        "customer_phone",
        "policy_number",
        "claim_type",
        "incident_date",
        "incident_time",
        "incident_location",
        "injuries",
        "other_vehicle",
        "amount",
        "description",
    }

    for field in direct_fields:

        if field in extraction_data:
            updated[field] = extraction_data[field]

    previous_corrections = updated.get(
        "corrections",
        [],
    )

    updated["corrections"] = [
        *previous_corrections,
        *extraction.corrections,
    ]

    previous_contradictions = updated.get(
        "contradictions",
        [],
    )

    updated["contradictions"] = [
        *previous_contradictions,
        *extraction.contradictions,
    ]

    updated["missing_information"] = (
        extraction.missing_information
    )

    updated["confidence"] = extraction.confidence

    updated["tool_results"] = (
        state.get("tool_results", {})
    )

    return updated