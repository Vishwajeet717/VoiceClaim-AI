from insurance.tools import (
    get_claim_history,
    get_customer,
    get_policy,
)


def main():
    phone = "9876543210"

    print()
    print("=" * 70)
    print("VOICECLAIM INSURANCE TOOL TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Customer lookup
    # ---------------------------------------------------------

    print()
    print("1. CUSTOMER LOOKUP")
    print("-" * 70)

    customer = get_customer(phone)

    if customer is None:
        print("Customer not found.")
        return

    print("Customer ID :", customer["id"])
    print("Name        :", customer["name"])
    print("Phone       :", customer["phone"])
    print("Email       :", customer["email"])

    # ---------------------------------------------------------
    # 2. Policy lookup
    # ---------------------------------------------------------

    print()
    print("2. POLICY LOOKUP")
    print("-" * 70)

    policy = get_policy(
        customer_id=customer["id"]
    )

    if policy is None:
        print("Policy not found.")
        return

    print("Policy ID      :", policy["id"])
    print("Policy Number  :", policy["policy_number"])
    print("Policy Type    :", policy["policy_type"])
    print("Status         :", policy["status"])
    print("Start Date     :", policy["start_date"])
    print("End Date       :", policy["end_date"])
    print("Coverage Limit :", policy["coverage_limit"])

    # ---------------------------------------------------------
    # 3. Claim history
    # ---------------------------------------------------------

    print()
    print("3. CLAIM HISTORY")
    print("-" * 70)

    claims = get_claim_history(
        customer_id=customer["id"],
        policy_id=policy["id"],
    )

    if not claims:
        print("No previous claims found.")
        return

    for claim in claims:
        print()
        print("Claim ID      :", claim["id"])
        print("Incident Date :", claim["incident_date"])
        print("Claim Type    :", claim["claim_type"])
        print("Amount        :", claim["amount"])
        print("Status        :", claim["status"])


if __name__ == "__main__":
    main()