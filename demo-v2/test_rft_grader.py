"""Test RFT grader with actual RFT data format before submission"""
import json

# Load the grader
with open("eval/zava_grader_rft.py") as f:
    grader_code = f.read()

# Execute to get the grade function
exec(grader_code)

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🧪 TESTING RFT GRADER WITH ACTUAL RFT DATA FORMAT")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# Test 1: Action scenario (from training data)
print("Test 1: Action Scenario (Refund)")
print("-" * 70)
sample1 = {}  # Empty during RFT
item1 = {
    "messages": [
        {"role": "user", "content": "I want to return order ORD-001"},
        {"role": "assistant", "content": "Policy: approved\nAction: refund\nAmount: $97.19\nI've processed a full refund of $97.19."}
    ],
    "tools": [
        {"name": "get_order_details"},
        {"name": "check_resolution_policy"},
        {"name": "calculate_resolution"}
    ],
    "expected_resolution": "Policy: approved. Action: refund. Amount: $97.19",
    "order_id": "ORD-001",
    "scenario_id": "S_001_001_refund"
}

score1 = grade(sample1, item1)
print(f"Expected: ~1.0 (perfect match)")
print(f"Actual:   {score1}")
print(f"Result:   {'✅ PASS' if score1 >= 0.95 else '❌ FAIL'}")
print()

# Test 2: Clarification scenario
print("Test 2: Clarification Scenario")
print("-" * 70)
sample2 = {}
item2 = {
    "messages": [
        {"role": "user", "content": "I want to return my sweater"},
        {"role": "assistant", "content": "Policy: clarification, please provide your order ID."}
    ],
    "tools": [],
    "expected_resolution": "Policy: clarification, please provide your order ID.",
    "scenario_id": "S_010_013_change_v3"
}

score2 = grade(sample2, item2)
print(f"Expected: 1.0 (perfect clarification)")
print(f"Actual:   {score2}")
print(f"Result:   {'✅ PASS' if score2 >= 0.95 else '❌ FAIL'}")
print()

# Test 3: Partial match scenario
print("Test 3: Partial Match (Wrong Amount)")
print("-" * 70)
sample3 = {}
item3 = {
    "messages": [
        {"role": "user", "content": "Return order ORD-001"},
        {"role": "assistant", "content": "Policy: approved\nAction: refund\nAmount: $50.00\nI've processed a refund."}
    ],
    "tools": [
        {"name": "get_order_details"},
        {"name": "check_resolution_policy"}
    ],
    "expected_resolution": "Policy: approved. Action: refund. Amount: $97.19",
    "order_id": "ORD-001"
}

score3 = grade(sample3, item3)
print(f"Expected: ~0.58 (action=0.45, amount=0, tools=0.13)")
print(f"Actual:   {score3}")
print(f"Result:   {'✅ PASS' if 0.4 <= score3 <= 0.7 else '❌ FAIL'}")
print()

# Test 4: Missing data (should not crash)
print("Test 4: Edge Case - Empty Messages")
print("-" * 70)
sample4 = {}
item4 = {
    "messages": [],
    "expected_resolution": "Policy: approved. Action: refund."
}

score4 = grade(sample4, item4)
print(f"Expected: 0.0 (no messages)")
print(f"Actual:   {score4}")
print(f"Result:   {'✅ PASS' if score4 == 0.0 else '❌ FAIL'}")
print()

# Test 5: Tool format variations
print("Test 5: Different Tool Formats")
print("-" * 70)
sample5 = {}
item5 = {
    "messages": [
        {"role": "user", "content": "Return ORD-001"},
        {"role": "assistant", "content": "Action: refund. Amount: $97.19"}
    ],
    "tools": [
        {"function": {"name": "get_order_details"}},
        {"tool_name": "check_resolution_policy"}
    ],
    "expected_resolution": "Action: refund. Amount: $97.19"
}

score5 = grade(sample5, item5)
print(f"Expected: ~0.93 (action=0.45, amount=0.35, tools=0.13)")
print(f"Actual:   {score5}")
print(f"Result:   {'✅ PASS' if score5 >= 0.85 else '❌ FAIL'}")
print()

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
all_pass = (
    score1 >= 0.95 and
    score2 >= 0.95 and
    0.4 <= score3 <= 0.7 and
    score4 == 0.0 and
    score5 >= 0.85
)
if all_pass:
    print("✅ ALL TESTS PASSED - Grader is ready for RFT submission!")
else:
    print("❌ SOME TESTS FAILED - Review grader logic before submitting")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

