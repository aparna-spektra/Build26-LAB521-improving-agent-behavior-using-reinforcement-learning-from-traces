# Training Dataset Changelog

## Version 2 (2026-05-26)

### Changes Made
Updated 11 scenarios to expect clarification instead of specific resolutions. These scenarios were missing order IDs in the user message, making them impossible for the agent to complete.

### Fixed Scenarios
All 11 scenarios now test the agent's ability to ask for missing information:

1. **S_012_015_change_v3** - Speaker return (no order ID)
2. **S_012_016_doesnt_v3** - Kettle return (no order ID)
3. **S_007_009_exchan_v3** - Running Jacket exchange (no order ID)
4. **S_004_005_late_d_v2** - LED Desk Lamp late delivery (no order ID)
5. **S_002_002_late_d_v3** - Keyboard late delivery (no order ID)
6. **S_011_014_buyers_v2** - Coffee Maker return (no order ID)
7. **S_004_006_change_v2** - Face Serum return (no order ID)
8. **S_003_004_change_v3** - Ceramic Mug return (no order ID)
9. **S_004_006_late_d_v3** - Face Serum late delivery (no order ID)
10. **S_004_006_person_v2** - Face Serum personal care (no order ID)
11. **S_010_012_doesnt_v3** - Hiking Boots return (no order ID)

### What Changed
For each scenario:
```json
{
  "expected_resolution": "Policy: clarification, please provide your order ID.",
  "expected_actions": {},
  "expected_amounts": {},
  "difficulty": "clarification"
}
```

### Rationale
- Each base scenario already has 2-3 variants (v1, v2, etc.) with order IDs that test the resolution logic
- These v2/v3 variants were failing 100% because the agent has no tool to lookup orders without an ID
- Converting them to clarification tests provides value:
  - Tests agent's ability to identify missing information
  - Tests graceful handling of incomplete requests
  - Tests proper use of clarification format
  - Trains the model to ask appropriate questions

### Files Modified
- `data/rft_next_train_v2.jsonl` - New version with fixed scenarios
- `data/rft_next_train.jsonl.backup_20260526_215955` - Backup of original

### Dataset Statistics
- Total scenarios: 192
- Action scenarios: 181 (94.3%)
- Clarification scenarios: 11 (5.7%)

### Impact on RFT Training
- **Before:** 11 scenarios (5.7%) would fail 100% of training runs (impossible to complete)
- **After:** These scenarios train the model to handle missing info gracefully
- **Expected improvement:** Better clarification behavior during inference
