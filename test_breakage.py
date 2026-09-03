from guardrails import SafetyGuard

guard = SafetyGuard()

def test_hallucinated_price():
    print("\n[TEST 1: Hallucinated / Injected Price]")
    # Catalog price is Rs. 1200 (120000 paise). Attacker/LLM claims Rs. 10 (1000 paise).
    passed, reason, _ = guard.validate_and_gate_order(
        product_id="prod_002",
        quantity=1,
        claimed_unit_price=1000,
        receipt_id="rcpt_attack_price_01"
    )
    assert not passed
    print(f"Outcome: {reason}")

def test_out_of_stock():
    print("\n[TEST 2: Out-of-Stock Item (USB-C Hub)]")
    # Catalog shows stock = 0 for prod_003
    passed, reason, _ = guard.validate_and_gate_order(
        product_id="prod_003",
        quantity=1,
        claimed_unit_price=80000,
        receipt_id="rcpt_stock_out_02"
    )
    assert not passed
    print(f"Outcome: {reason}")

def test_budget_overflow():
    print("\n[TEST 3: Budget Fence Exceeded]")
    # Keyboard is Rs. 4,500 (450000 paise). Safety cap is Rs. 2,000 (200000 paise).
    passed, reason, _ = guard.validate_and_gate_order(
        product_id="prod_001",
        quantity=1,
        claimed_unit_price=450000,
        receipt_id="rcpt_budget_exceeded_03"
    )
    assert not passed
    print(f"Outcome: {reason}")

def test_duplicate_charge_attack():
    print("\n[TEST 4: Idempotency Replay Attack / Loop]")
    # First attempt: valid purchase (Desk Mat Rs. 450)
    passed1, reason1, _ = guard.validate_and_gate_order(
        product_id="prod_004",
        quantity=1,
        claimed_unit_price=45000,
        receipt_id="rcpt_unique_999"
    )
    assert passed1
    print(f"First Attempt: {reason1}")

    # Second attempt: same receipt ID (network retry or infinite LLM loop)
    passed2, reason2, _ = guard.validate_and_gate_order(
        product_id="prod_004",
        quantity=1,
        claimed_unit_price=45000,
        receipt_id="rcpt_unique_999"
    )
    assert not passed2
    print(f"Second Attempt (Replay): {reason2}")

if __name__ == "__main__":
    test_hallucinated_price()
    test_out_of_stock()
    test_budget_overflow()
    test_duplicate_charge_attack()
    print("\n==========================================")
    print("All 4 edge cases caught deterministically.")
    print("Check audit_trail.jsonl for complete immutable logs.")
    print("==========================================")