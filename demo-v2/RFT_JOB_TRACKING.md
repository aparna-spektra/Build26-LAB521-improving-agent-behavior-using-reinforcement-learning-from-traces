# RFT Job Tracking - Phase 3

## ❌ Previous Job (Canceled - Tool Configuration Bug)

**Job ID:** `o4-mini-2025-04-16.ftjob-62b56b829c5745fb9b4fa5963e040a83-zava-next-rft-20260526-233605`

**Status:** Canceled

**Issue:** Tool URLs incorrectly configured with full path instead of base URL
- Tools were not being called during training
- All evaluation scores = 0.0
- No positive reinforcement signal

**Bug:** `server_url: "{TOOL_URL}/tool/get_order_details"` (WRONG)
- Foundry appends /{tool_name}, resulting in: `.../tool/get_order_details/get_order_details` → 404

---

## ✅ Current RFT Job (Corrected)

**Job ID:** `o4-mini-2025-04-16.ftjob-873594fb42c941fbac8e86f725936363-zava-next-rft-20260527-021749`

**Submitted:** 2026-05-27 02:17:49

**Status:** Running (training in progress)

**Configuration:**
- **Base Model:** o4-mini (reasoning model)
- **Method:** reinforcement
- **Training Data:** data/rft_next_train_v2.jsonl (192 scenarios)
  - 181 action scenarios (94.3%)
  - 11 clarification scenarios (5.7%)
- **Validation Data:** data/rft_next_val_v2.jsonl (62 scenarios)
  - 52 action scenarios (84%)
  - 10 clarification scenarios (16%)
- **Grader:** eval/zava_grader_rft.py
  - Pass threshold: 0.80
  - Scoring: 45% action + 35% amounts + 20% tools
  - Data format: item['messages'] for agent output
- **Tools:** 6 tools from https://zava-next-tools-omkarm.azurewebsites.net/tool
  - ✅ FIXED: Base URL only (Foundry appends /{tool_name})
  - get_order_details
  - get_fulfillment_status
  - check_resolution_policy
  - check_inventory
  - calculate_resolution
  - submit_resolution
- **Hyperparameters:**
  - n_epochs: 3
  - learning_rate_multiplier: 1.0
  - compute_multiplier: 1.5
  - reasoning_effort: medium
  - max_episode_steps: 5
  - eval_interval: 5
  - eval_samples: 10

## Expected Timeline

- **Submission:** ✅ Complete (2026-05-27 02:17)
- **Training:** ⏳ In Progress (2-4 hours expected)
- **Completion:** Est. 2026-05-27 04:17 - 06:17
- **Deployment:** Pending (after training completes)
- **Evaluation:** Pending (use phase2_base_evaluations.ipynb)

## Critical Monitoring Points

**What to Check in First Evaluation (after ~15-20 minutes):**

1. **Tool Calls Being Made?**
   - Evaluation should show agent using tools
   - Look for tool names in execution logs

2. **Grader Scores > 0?**
   - Should see scores ranging from 0.3 to 1.0
   - NOT all zeros anymore!
   - Expected: ~40-60% of scenarios score ≥0.80 on first eval

3. **Training Progress?**
   - Reward metrics should increase over time
   - Success rate should improve across epochs

## Monitoring

To check job status:
```python
from openai import AzureOpenAI
client = AzureOpenAI(...)
job_status = client.fine_tuning.jobs.retrieve("o4-mini-2025-04-16.ftjob-873594fb42c941fbac8e86f725936363-zava-next-rft-20260527-021749")
print(job_status.status)
```

Or use the notebook: `notebooks/phase3_submit_rft.ipynb` Cell 13 (Monitor Job Progress)

## Next Steps (After Completion)

1. **Verify Training Metrics**
   - Check that evaluation scores were NON-ZERO
   - Confirm tools were being called
   - Verify reward improved over epochs

2. **Retrieve Fine-Tuned Model ID**
   - Get from `job_status.fine_tuned_model`
   - Format: `o4-mini:<deployment-id>-zava-next-rft-20260527-021749`

3. **Deploy as Hosted Agent**
   - Create new agent deployment pointing to fine-tuned model
   - Use same agent code and tools as baseline o4-mini

4. **Run Post-RFT Evaluation**
   - Open `notebooks/phase2_base_evaluations.ipynb`
   - Add RFT model to agent list
   - Run evaluation on same 62 validation scenarios
   - Compare: baseline o4-mini vs RFT o4-mini

5. **Expected Improvements**
   - Overall pass rate: +15-25% improvement over baseline
   - Decision correctness: Significant gain (policy application)
   - Financial accuracy: Moderate gain (restocking fees)
   - Format compliance: Slight gain (consistent output)

## Key Fixes Applied

1. **Tool Configuration** (Cell 9)
   - Changed from: `server_url: "{TOOL_URL}/tool/get_order_details"`
   - Changed to: `server_url: "{TOOL_URL}/tool"`
   - Foundry now correctly calls: `{TOOL_URL}/tool/{tool_name}`

2. **Grader Data Format** (eval/zava_grader_rft.py)
   - Extracts agent response from `item['messages']` (not `sample`)
   - Handles clarification scenarios
   - Robust tool call extraction

## Reference

Successful reference implementation:
- Notebook: https://github.com/microsoft-foundry/fine-tuning/blob/main/Demos/ZavaRetailAgent/demo.ipynb
- Previous run: `o4-mini-2025-04-16.ft-1839d286a0654e459697cd02cb8eb9a4-zava-next-rft`
- Training time: ~3 hours

## Notes

- First evaluation run should show NON-ZERO scores (this confirms tools are working!)
- Training with tool-calling should show meaningful learning progress
- Monitor evaluation scores every 5 steps to ensure positive trend
