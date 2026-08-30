from agent.state import ClaimState


def build_claim_summary(
    state: ClaimState,
) -> str:
    incident_date = (
        state.get("incident_date")
        or "not provided"
    )

    incident_time = (
        state.get("incident_time")
        or "not provided"
    )

    injuries = state.get("injuries")

    if injuries is True:
        injury_text = "an injury was reported"
    elif injuries is False:
        injury_text = "no injuries were reported"
    else:
        injury_text = "injury information was not provided"

    other_vehicle = state.get(
        "other_vehicle"
    )

    if other_vehicle is True:
        vehicle_text = "another vehicle was involved"
    elif other_vehicle is False:
        vehicle_text = "no other vehicle was involved"
    else:
        vehicle_text = "information about another vehicle is not available"

    amount = state.get("amount")

    if amount is not None:
        amount_text = (
            f"the estimated damage is ₹{amount:,.0f}"
        )
    else:
        amount_text = (
            "the estimated damage amount was not provided"
        )

    return (
        f"I have the incident date as {incident_date}, "
        f"at approximately {incident_time}. "
        f"{injury_text}, {vehicle_text}, and "
        f"{amount_text}. "
        "Is all of that information correct?"
    )