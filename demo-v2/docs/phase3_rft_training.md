# Phase 3: Reinforcement Fine-Tuning (RFT)

**Demo Time:** 10-12 minutes  
**Status:** Planned 📝  

---

## 🎯 Objectives

By the end of Phase 3, the audience should understand:
1. How to prepare RFT training data from evaluation failures
2. How to submit RFT jobs on Azure AI Foundry
3. How to deploy fine-tuned models as hosted agents
4. The performance improvement from RFT training
5. Which failure modes RFT resolves

---

## 📋 Prerequisites

- Phase 2 complete (baseline evaluations done)
- Failure scenarios identified
- Best base model selected (gpt-4-1-mini or o4-mini)
- Full agentic grader ready (`eval/zava_grader_agentic.py`)

---

## 🎬 Demo Script

### 1. Extract Training Data from Failures (3 min)

**Demo:** Open `notebooks/phase3_01_prepare_rft_data.ipynb`

**Explain the strategy:**
- **Failed scenarios:** 22 scenarios where gpt-4-1-mini scored <0.8
- **Edge cases:** 10-15 scenarios that passed but were close (0.8-0.85)
- **Total:** 35-40 training examples

**Why these scenarios?**
- RFT learns from mistakes
- Edge cases prevent overfitting
- Small dataset is sufficient (RL is sample-efficient)

**Cell 1: Load baseline results**
```python
# Load previous eval results
with open("eval/eval_results_latest.json") as f:
    results = json.load(f)

# Filter for gpt-4-1-mini
model_results = results["gpt-4-1-mini"]

# Extract failed scenarios
failed = [
    r for r in model_results 
    if r["zava_quality"] < 0.8
]
print(f"Found {len(failed)} failed scenarios")
```

**Cell 2: Extract edge cases**
```python
# Scenarios that passed but were close
edge_cases = [
    r for r in model_results
    if 0.8 <= r["zava_quality"] < 0.85
]
print(f"Found {len(edge_cases)} edge cases")
```

**Cell 3: Create training dataset**
```python
# Combine failures + edge cases
training_examples = failed + edge_cases[:15]

# Format for RFT
# Each example includes:
# - Input (messages)
# - Expected output (ground truth)
# - Reward signal (0.0 - 1.0)

rft_data = []
for ex in training_examples:
    rft_data.append({
        "messages": ex["input"],
        "expected_actions": ex["expected_actions"],
        "scenario_id": ex["scenario_id"]
    })

# Save
with open("eval/rft_training_examples.jsonl", "w") as f:
    for item in rft_data:
        f.write(json.dumps(item) + "\n")

print(f"✅ Created {len(rft_data)} training examples")
```

**Result:** `eval/rft_training_examples.jsonl` (35-40 examples)

---

### 2. Explain RFT Grader Difference (2 min)

**Show:** Comparison of graders

**Phase 2 Grader (`zava_grader_response.py`):**
- Response-only evaluation
- Scores final output text
- Used for baseline evals

**Phase 3 Grader (`zava_grader_agentic.py`):**
- Full agentic validation
- Checks tool-call sequence
- Validates intermediate steps
- Provides reward signal for RL
- Used during RFT training

**Key difference:** RFT needs to know not just if the answer is right, but if the *reasoning path* is right.

**Example:**
```
Correct answer via wrong path:
- Tool sequence: get_order → submit (skipped policy check)
- Final answer: Correct refund amount
- Response-only score: 1.0 ✅
- Agentic score: 0.6 ❌ (penalized for skipping tools)

RFT learns: Must call tools in correct sequence
```

---

### 3. Submit RFT Job (2 min)

**Demo:** Open `notebooks/phase3_02_submit_rft_job.ipynb`

**Cell 1: Configure RFT job**
```python
BASE_MODEL = "o4-mini"  # Or gpt-4-1-mini
TRAINING_DATA = "eval/rft_training_examples.jsonl"
GRADER = "eval/zava_grader_agentic.py"

# RFT hyperparameters
config = {
    "learning_rate": 1e-5,
    "num_epochs": 3,
    "reward_threshold": 0.8,  # Target score
    "kl_penalty": 0.01  # Keep model close to base
}
```

**Cell 2: Submit to Foundry**
```python
# Option 1: Via SDK (if available)
rft_job = client.fine_tuning.create(
    model=BASE_MODEL,
    training_file=TRAINING_DATA,
    grader=GRADER,
    config=config
)

# Option 2: Via Portal
# Go to Fine-tuning → Create job → Select RFT
```

**Show:** Foundry portal Fine-tuning page
- Training job appears
- Status: Queued → Running
- Expected time: 2-4 hours

---

### 4. Monitor Training (1 min)

**Demo:** Show training metrics (pre-recorded or live if time permits)

**Metrics to watch:**
- **Reward curve:** Should increase over epochs
- **KL divergence:** Should stay low (model not drifting too far from base)
- **Loss curve:** Should decrease

**Typical training:**
- Epoch 1: Reward 0.55 → 0.68
- Epoch 2: Reward 0.68 → 0.75
- Epoch 3: Reward 0.75 → 0.82

**Key Insight:** "With just 35-40 examples, RFT teaches the model the right behavior patterns"

---

### 5. Deploy Fine-Tuned Model (1 min)

**Demo:** Deploy fine-tuned model as agent

```bash
# Fine-tuned model appears in Foundry after training
# Deploy as new agent

cd demo-v2
./scripts/deploy_agent.sh zava-next o4-mini-rft
```

**Agent name:** `zava-next-o4-mini-rft`

**Explain:** Same agent codebase, different model deployment

---

### 6. Evaluate Fine-Tuned Model (3 min)

**Demo:** Open `notebooks/phase3_03_evaluate_rft.ipynb`

**Run same evaluation:**
- Same 62 validation scenarios
- Same grader (zava_quality)
- Compare with baseline o4-mini

**Expected Results:**

| Model | Overall Pass Rate | Zava Quality | Improvement |
|-------|------------------|--------------|-------------|
| **o4-mini (base)** | 46.0% | 53.2% | Baseline |
| **o4-mini-rft** | 68.5% | 76.8% | +22.5% 🚀 |

**Per-Criteria Improvement:**

| Criterion | Base | RFT | Gain |
|-----------|------|-----|------|
| Decision Correctness | 60% | 82% | +22% |
| Financial Accuracy | 78% | 92% | +14% |
| Format Compliance | 60% | 74% | +14% |

**Key Insights:**
- **Decision correctness improved most** (RFT learned the policies)
- **Financial accuracy improved** (learned fee calculations)
- **Format compliance improved** (learned structured output)

---

### 7. Show Before/After Examples (2 min)

**Demo:** Pick 2-3 failed scenarios, show how RFT fixed them

**Example 1: Sale Item Return (Defective)**

**Baseline o4-mini:**
```
Action: REFUND ORDER-123 ITEM-456 AMOUNT $89.99
❌ Wrong — should be STORE_CREDIT (sale items are final sale)
```

**After RFT:**
```
Action: STORE_CREDIT ORDER-123 ITEM-456 AMOUNT $89.99
✅ Correct — learned sale item exception
```

**Example 2: Restocking Fee Calculation**

**Baseline o4-mini:**
```
Action: REFUND ORDER-234 ITEM-567 AMOUNT $200.00 FEE $0
❌ Wrong — Gold tier customer should have 7.5% fee ($15)
```

**After RFT:**
```
Action: REFUND ORDER-234 ITEM-567 AMOUNT $185.00 FEE $15.00
✅ Correct — learned tier-specific fee logic
```

**Example 3: Multi-Item Order**

**Baseline o4-mini:**
```
Action: REFUND ORDER-345 AMOUNT $150.00
❌ Incomplete — order has 2 items, missing per-item resolution
```

**After RFT:**
```
Action: REFUND ORDER-345 ITEM-678 AMOUNT $100.00 FEE $0
Action: DENY ORDER-345 ITEM-789 REASON outside_return_window
✅ Correct — handled each item separately
```

---

## ✅ Success Criteria

At the end of Phase 3, verify:
- [ ] Training data extraction is demonstrated
- [ ] RFT job submission is shown
- [ ] Fine-tuned model is deployed
- [ ] Post-RFT evaluation shows improvement
- [ ] Specific failure modes are resolved
- [ ] Comparison table clearly shows gains

---

## 📁 Files & Resources

| File | Purpose |
|------|---------|
| `notebooks/phase3_01_prepare_rft_data.ipynb` | Extract training examples |
| `notebooks/phase3_02_submit_rft_job.ipynb` | Submit RFT training job |
| `notebooks/phase3_03_evaluate_rft.ipynb` | Eval fine-tuned model |
| `eval/rft_training_examples.jsonl` | RFT training data |
| `eval/zava_grader_agentic.py` | Full grader with tool validation |
| `eval/rft_comparison_results.json` | Before/after comparison |
| `docs/RFT_TRAINING.md` | Detailed RFT guide (to be created) |

---

## 🐛 Common Issues

### RFT job fails during training
- **Check:** Training data format is correct (JSONL)
- **Check:** Grader function signature matches requirements
- **Check:** Model deployment exists

### Fine-tuned model doesn't improve
- **Issue:** Training data too small or not representative
- **Fix:** Add more failure examples (40-50)
- **Fix:** Include more edge cases

### Eval shows regression on some scenarios
- **Expected:** Some tradeoffs are normal
- **Check:** Overall improvement > 15%
- **Analyze:** Which scenarios regressed and why

---

## 🔗 Next Phase

**Phase 4: LoRA Training (Qwen3-32B)**

Now that we've shown RFT on a cloud model, let's apply LoRA training to an open-source model for even more control.

[→ Go to Phase 4 Guide](phase4_lora_training.md)
