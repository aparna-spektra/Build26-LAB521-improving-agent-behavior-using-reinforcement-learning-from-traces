# RFT Platform Bug Reports

Tracking issues encountered during agentic RFT experiments on Microsoft Foundry.

---

## BUG-001: Endpoint grader job hangs indefinitely in post-training validation

**Date:** 2026-04-19  
**Job ID:** `ftjob-eb89e8ced85842a4b79bcf5427b1b1e8`  
**Resource:** ignite-agenticft-lab-resource (DefaultResourceGroup-NCUS, FT Team Sub)  
**Model:** o4-mini-2025-04-16  
**Suffix:** zava-v5-eg70  

### Description
Agentic RFT job with endpoint grader completed all 30 training steps successfully (train_mean_reward reached 0.866 at step 30), then hung indefinitely in post-training processing. No completion event, no model saved. Job remained in `running` status for 37+ hours after the last training step.

### Timeline
- Apr 17 15:14 — Job enqueued
- Apr 17 20:53 — Training started
- Apr 17 21:15 — Step 1: reward = -0.007
- Apr 17 23:22 — Step 30: reward = 0.866 ← last event
- Apr 19 12:41 — Cancelled after 37+ hours with no further progress

### Training step cadence
Steps ran at ~22 min/step (steps 10-30), consistent with endpoint grader HTTP overhead. The training phase itself was healthy.

### Suspected cause
Post-training validation eval attempts to call the endpoint grader for each validation example. If the endpoint grader times out, returns errors, or the eval framework doesn't handle HTTP failures gracefully, the job stalls silently. The grader endpoint was verified healthy (HTTP 200) throughout.

### Comparison
- `ftjob-5c828e9b` (same dataset, Python grader @0.90) completed in ~145 minutes total including post-training.
- The endpoint grader job trained at ~22 min/step vs ~20 min/step for Python grader — only slightly slower during training, but post-training is where it hung.

### Impact
- 30 steps of successful GPU training wasted (no model artifact)
- No error message or indication of what caused the hang
- Had to manually cancel

### Requested fixes
1. Timeout on post-training eval — if eval hasn't completed in N minutes, save the model anyway
2. Surface errors from endpoint grader eval in the events stream
3. Allow model extraction from cancelled jobs that completed training (checkpoints existed)

### Workaround
Use Python grader instead of endpoint grader. If endpoint grader is required, scale the endpoint for high throughput and add aggressive timeout handling.

---

## BUG-002: Validation evals do not execute tool calls

**Date:** 2026-04-17  
**Affects:** All agentic RFT jobs with tools  

### Description
During agentic RFT, training rollouts correctly call tool endpoints via `server_url` and receive results. However, the validation evals shown in Foundry UI do NOT execute the tool call loop. The eval captures only the model's first response (typically a tool call request), which means:

- `valid_reward_mean` is misleadingly low (~0) since the grader sees an incomplete response
- Eval pass rates in the UI show ~0% even when training is working perfectly
- Checkpoint selection based on `full_valid_mean_reward` may be suboptimal

### Workaround
Monitor `train_mean_reward` instead. After training, evaluate checkpoints with a local harness that executes the full tool loop.

---