# Validation Dataset Changelog

## Version 2 (2026-05-26)

### Changes Made
Updated 10 scenarios to expect clarification instead of specific resolutions. These scenarios were missing order IDs in the user message, making them impossible for the agent to complete.

### Fixed Scenarios
All 10 scenarios now test the agent's ability to ask for missing information:

1. **S_010_013_change_v3** - Bluetooth Speaker return (no order ID)
2. **S_004_006_buyers_v3** - Face Serum Set return (no order ID)
3. **S_003_003_exchan_v3** - Mechanical Keyboard exchange (no order ID)
4. **S_007_009_buyers_v2** - Running Jacket return (no order ID)
5. **S_004_005_exchan_v3** - LED Desk Lamp exchange (no order ID)
6. **S_006_008_change_v2** - Yoga Mat return (no order ID)
7. **S_006_008_buyers_v3** - Yoga Mat return (no order ID)
8. **S_007_009_doesnt_v3** - Running Jacket return (doesn't fit)
9. **S_009_011_defect_v3** - Water Bottle defective (no order ID)
10. **S_010_012_defect_v2** - Hiking Boots defective (no order ID)

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

### Grader Updates
Updated `eval/zava_grader_response.py` to handle clarification scenarios:
- Detects `expected_resolution` starting with "Policy: clarification"
- Scores based on:
  - Presence of "Policy: clarification" marker
  - Mention of "order ID" in response
  - Full score (1.0) if both present
  - Partial score (0.7) if one present
  - Low score (0.3) if neither present

### Files Modified
- `data/rft_next_val_v2.jsonl` - New version with fixed scenarios
- `data/rft_next_val.jsonl.backup_20260526_205745` - Backup of original
- `eval/zava_grader_response.py` - Added clarification scoring logic
- `notebooks/phase2_base_evaluations.ipynb` - Updated to use v2 dataset

### Impact on Evaluation Scores
- **Before:** 10 scenarios (16% of dataset) failed for all models (impossible to complete)
- **After:** These scenarios test a different capability (clarification) and should pass for good models
- **Expected improvement:** ~5-8% increase in overall scores for models that properly ask for clarification

### Dataset Statistics
- Total scenarios: 62
- Action scenarios: 52 (84%)
- Clarification scenarios: 10 (16%)
- Difficulty breakdown:
  - Easy: TBD
  - Medium: TBD
  - Hard: TBD
  - Clarification: 10
