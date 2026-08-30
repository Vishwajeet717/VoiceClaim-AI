from datetime import date, datetime
from decimal import Decimal
from typing import Any


REPORTING_WINDOW_DAYS = 30
MANUAL_ASSESSMENT_AMOUNT = Decimal("500000")


def normalize_date(
    value: date | datetime | str | None,
) -> date | None:
    """
    Convert supported date representations into datetime.date.

    Accepts:
    - datetime.date
    - datetime.datetime
    - ISO date strings such as '2026-08-21'
    - None
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return None

        try:
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(
                f"Invalid date format: {value}. "
                "Expected YYYY-MM-DD."
            ) from exc

    raise TypeError(
        f"Unsupported date type: {type(value).__name__}"
    )


def check_coverage(
    policy: dict[str, Any],
    incident_date: date | datetime | str | None,
    claim_type: str | None,
    injuries: bool | None = None,
    amount: Decimal | float | int | None = None,
    reported_date: date | datetime | str | None = None,
) -> dict[str, Any]:
    """
    Perform a preliminary insurance coverage assessment.

    IMPORTANT:
    This function does NOT approve or reject a claim.

    It applies the project's demo policy rules and returns
    structured findings for the action/risk engine.
    """

    reasons: list[str] = []
    warnings: list[str] = []
    missing_information: list[str] = []

    escalation_required = False
    manual_review_required = False

    # ---------------------------------------------------------
    # Normalize dates at the system boundary
    # ---------------------------------------------------------

    incident_date = normalize_date(incident_date)
    reported_date = normalize_date(reported_date)

    # ---------------------------------------------------------
    # Validate required policy information
    # ---------------------------------------------------------

    if not policy:
        return {
            "coverage_status": "unable_to_assess",
            "reason": "No policy information was provided.",
            "reasons": [],
            "warnings": [],
            "missing_information": ["policy"],
            "manual_review_required": False,
            "escalation_required": True,
        }

    if incident_date is None:
        missing_information.append("incident_date")

    if not claim_type:
        missing_information.append("claim_type")

    if missing_information:
        return {
            "coverage_status": "information_required",
            "reason": (
                "Additional incident information is required "
                "before coverage can be assessed."
            ),
            "reasons": [],
            "warnings": [],
            "missing_information": missing_information,
            "manual_review_required": False,
            "escalation_required": False,
        }

    # ---------------------------------------------------------
    # Normalize policy dates
    # ---------------------------------------------------------

    policy_start = normalize_date(
        policy["start_date"]
    )

    policy_end = normalize_date(
        policy["end_date"]
    )

    if policy_start is None or policy_end is None:
        return {
            "coverage_status": "unable_to_assess",
            "reason": "Policy dates are incomplete.",
            "reasons": [],
            "warnings": [],
            "missing_information": ["policy_dates"],
            "manual_review_required": False,
            "escalation_required": True,
        }

    # ---------------------------------------------------------
    # Policy active on incident date
    # ---------------------------------------------------------

    policy_active = (
        policy_start <= incident_date <= policy_end
        and str(
            policy.get("status", "")
        ).lower() == "active"
    )

    if not policy_active:
        reasons.append(
            "The policy was not active on the incident date."
        )

        return {
            "coverage_status": (
                "not_eligible_under_available_rules"
            ),
            "reason": (
                "The policy was not active on the incident date."
            ),
            "reasons": reasons,
            "warnings": warnings,
            "missing_information": [],
            "policy_active": False,
            "reported_within_30_days": None,
            "manual_review_required": False,
            "escalation_required": True,
            "incident_date": incident_date.isoformat(),
        }

    reasons.append(
        "The policy was active on the incident date."
    )

    # ---------------------------------------------------------
    # Reporting window
    # ---------------------------------------------------------

    if reported_date is None:
        reported_date = date.today()

    days_since_incident = (
        reported_date - incident_date
    ).days

    reported_within_window = (
        0 <= days_since_incident <= REPORTING_WINDOW_DAYS
    )

    if reported_within_window:

        reasons.append(
            "The incident was reported within the "
            "policy's 30-day reporting guideline."
        )

    elif days_since_incident < 0:

        warnings.append(
            "The reported date is earlier than the incident date."
        )

        escalation_required = True

    else:

        warnings.append(
            "The incident is outside the policy's "
            "30-day reporting guideline."
        )

        escalation_required = True

    # ---------------------------------------------------------
    # Bodily injury
    # ---------------------------------------------------------

    if injuries is True:

        warnings.append(
            "Bodily injury was reported and the policy "
            "requires human claims-specialist review."
        )

        escalation_required = True
        manual_review_required = True

    # ---------------------------------------------------------
    # Claim type
    # ---------------------------------------------------------

    normalized_claim_type = (
        claim_type.strip().lower()
    )

    if normalized_claim_type in {
        "motor_collision",
        "collision",
        "vehicle_collision",
        "accidental_damage",
    }:

        reasons.append(
            "The claim type is consistent with accidental "
            "collision damage covered by the available "
            "policy wording."
        )

    else:

        warnings.append(
            "The available policy wording does not explicitly "
            "establish coverage for this claim type."
        )

        escalation_required = True

    # ---------------------------------------------------------
    # Claim amount
    # ---------------------------------------------------------

    normalized_amount: Decimal | None = None

    if amount is not None:

        normalized_amount = Decimal(str(amount))

        if normalized_amount < 0:
            raise ValueError(
                "Claim amount cannot be negative."
            )

        if normalized_amount > MANUAL_ASSESSMENT_AMOUNT:

            warnings.append(
                "The claim amount exceeds INR 500000 and "
                "requires manual assessment."
            )

            manual_review_required = True
            escalation_required = True

        else:

            reasons.append(
                "The claim amount does not exceed the "
                "INR 500000 manual-assessment threshold."
            )

    # ---------------------------------------------------------
    # Final preliminary status
    # ---------------------------------------------------------

    if escalation_required:

        coverage_status = (
            "potentially_covered_requires_review"
        )

    else:

        coverage_status = "potentially_covered"

    return {
        "coverage_status": coverage_status,
        "reason": (
            "The available policy information indicates that "
            "the claim may be covered, subject to the policy "
            "terms, exclusions, and required review."
        ),
        "reasons": reasons,
        "warnings": warnings,
        "missing_information": missing_information,
        "policy_active": policy_active,
        "reported_within_30_days": reported_within_window,
        "days_since_incident": days_since_incident,
        "manual_review_required": manual_review_required,
        "escalation_required": escalation_required,
        "claim_type": normalized_claim_type,
        "amount": (
            str(normalized_amount)
            if normalized_amount is not None
            else None
        ),
        "incident_date": incident_date.isoformat(),
        "reported_date": reported_date.isoformat(),
    }