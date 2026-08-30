from datetime import date
from decimal import Decimal

from insurance.coverage import check_coverage
from insurance.tools import get_customer, get_policy


def print_result(title: str, result: dict) -> None:
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    for key, value in result.items():
        print(f"{key}: {value}")


def main():
    # ---------------------------------------------------------
    # Get the real demo policy from Supabase
    # ---------------------------------------------------------

    customer = get_customer("9876543210")

    if customer is None:
        print("Customer not found.")
        return

    policy = get_policy(
        customer_id=customer["id"]
    )

    if policy is None:
        print("Policy not found.")
        return

    # ---------------------------------------------------------
    # Test 1 — Normal collision
    # ---------------------------------------------------------

    normal_collision = check_coverage(
        policy=policy,
        incident_date=date(2026, 8, 20),
        claim_type="motor_collision",
        injuries=False,
        amount=Decimal("85000"),
        reported_date=date(2026, 8, 22),
    )

    print_result(
        "TEST 1 — NORMAL COLLISION",
        normal_collision,
    )

    # ---------------------------------------------------------
    # Test 2 — Bodily injury
    # ---------------------------------------------------------

    bodily_injury = check_coverage(
        policy=policy,
        incident_date=date(2026, 8, 20),
        claim_type="motor_collision",
        injuries=True,
        amount=Decimal("85000"),
        reported_date=date(2026, 8, 22),
    )

    print_result(
        "TEST 2 — BODILY INJURY",
        bodily_injury,
    )

    # ---------------------------------------------------------
    # Test 3 — High-value claim
    # ---------------------------------------------------------

    high_value = check_coverage(
        policy=policy,
        incident_date=date(2026, 8, 20),
        claim_type="motor_collision",
        injuries=False,
        amount=Decimal("750000"),
        reported_date=date(2026, 8, 22),
    )

    print_result(
        "TEST 3 — HIGH VALUE CLAIM",
        high_value,
    )

    # ---------------------------------------------------------
    # Test 4 — Outside reporting window
    # ---------------------------------------------------------

    late_claim = check_coverage(
        policy=policy,
        incident_date=date(2026, 7, 1),
        claim_type="motor_collision",
        injuries=False,
        amount=Decimal("85000"),
        reported_date=date(2026, 8, 22),
    )

    print_result(
        "TEST 4 — LATE REPORT",
        late_claim,
    )

    # ---------------------------------------------------------
    # Test 5 — Unknown claim type
    # ---------------------------------------------------------

    unknown_claim = check_coverage(
        policy=policy,
        incident_date=date(2026, 8, 20),
        claim_type="meteor_damage",
        injuries=False,
        amount=Decimal("85000"),
        reported_date=date(2026, 8, 22),
    )

    print_result(
        "TEST 5 — UNKNOWN CLAIM TYPE",
        unknown_claim,
    )


if __name__ == "__main__":
    main()