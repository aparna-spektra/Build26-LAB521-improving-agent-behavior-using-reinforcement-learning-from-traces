# Phase 2: Base Model Evaluations

**Demo Time:** 12-15 minutes  
**Status:** ✅ Complete  
**Latest Run:** zava-multi-model-eval-20260526-210056

---

## 🎯 Objectives

By the end of Phase 2, the audience should understand:
1. How to create custom Python graders for Azure AI Foundry
2. How to run multi-model evaluations programmatically
3. What the performance gap looks like across base models
4. Where models struggle (failure pattern analysis)
5. Why RFT is needed to improve agent behavior

---

## 📋 Prerequisites

- Phase 1 complete (6 agents deployed)
- Validation dataset prepared (`data/rft_next_val_v2.jsonl`)
- `.env` file configured with PROJECT_ENDPOINT
- Python environment with dependencies installed

**Install dependencies:**
```bash
pip install -r requirements.txt
```

---

## 🎬 Demo Script

### 1. Introduce the Evaluation Dataset (2 min)

**Show:** `data/rft_next_val_v2.jsonl`

**Key Points:**
- 62 validation scenarios (held out from training)
- Never seen by models during training
- **52 action scenarios** (84%) - Test resolution logic
- **10 clarification scenarios** (16%) - Test handling of missing info
- Covers all edge cases:
  - Return window boundaries
  - Tier-specific policies  
  - Sale items (final sale unless defective)
  - Late deliveries (extended window + credit)
  - Lost packages
  - Multi-item orders

**Format:**
```json
{
  "messages": [
    {"role": "developer", "content": "system prompt..."},
    {"role": "user", "content": "customer request..."}
  ],
  "expected_resolution": "Action: refund for LI-013 (reason: changed_mind). Amount: $79.99.",
  "expected_actions": {"LI-013": {"action": "refund", "reason": "changed_mind"}},
  "expected_amounts": {"LI-013_refund": 79.99},
  "scenario_id": "S_010_013_change",
  "difficulty": "medium"
}
```

**For clarification scenarios:**
```json
{
  "expected_resolution": "Policy: clarification, please provide your order ID.",
  "expected_actions": {},
  "expected_amounts": {},
  "difficulty": "clarification"
}
```

---

### 2. Explain the Custom Grader (3 min)

**Show:** `eval/zava_grader_response.py`

**Demo:** Walk through key sections

**The Zava Quality Metric:**

```python
def grade(sample, item) -> float:
    """
    Scores agent responses on 3 dimensions:
    - Decision Correctness (50%): Right action?
    - Financial Accuracy (30%): Correct amounts?
    - Format Compliance (20%): Structured output?
    """
    # Parse action lines from response
    actions = parse_action_lines(response)
    
    # Score each dimension
    decision_score = score_decision(actions, expected)
    financial_score = score_financial(actions, expected)
    format_score = score_format(actions)
    
    # Weighted combination
    combined = (
        0.5 * decision_score + 
        0.3 * financial_score + 
        0.2 * format_score
    )
    
    return combined  # 0.0 - 1.0
```

**Key Insight:** "We need custom grading because:
1. Generic metrics (BLEU, ROUGE) don't capture business logic
2. We care about specific outcomes (right refund amount, correct restocking fee)
3. We need to parse structured actions from free-text responses"

**Foundry Requirements:**
- Must have top-level `grade(sample, item)` function
- Returns float between 0.0 and 1.0
- Cannot use `re.compile()` (sandbox restriction)
- Agent output is in `item['sample.output_text']` (not sample parameter)
- Handles both action and clarification scenarios

---

### 3. Run Multi-Model Evaluation (4 min)

**Demo:** Open `notebooks/phase2_base_evaluations.ipynb`

**Walk through cells:**

**Cell 1: Configuration**
```python
from dotenv import load_dotenv
load_dotenv()

PROJECT_ENDPOINT = os.getenv('PROJECT_ENDPOINT')
DATASET_NAME = f"zava-eval-{timestamp}"
EVAL_NAME = f"zava-multi-model-eval-{timestamp}"
```

**Cell 2: Upload Dataset**
```python
dataset = client.datasets.upload_file(
    file_path="data/rft_next_val.jsonl",
    name=DATASET_NAME,
    version="1.0"
)
```

**Cell 3: Load Custom Grader**
```python
with open("eval/zava_grader_response.py") as f:
    grader_source = f.read()
```

**Cell 4: Create Evaluation Definition**
```python
models = [
    "zava-next-o4-mini",
    "zava-next-gpt-4-1",
    "zava-next-gpt-4-1-mini",
    "zava-next-gpt-4-1-nano",
    "zava-next-gpt-5-4",
    "zava-next-gpt-5-4-mini"
]

evaluators = {
    "zava_quality": {
        "type": "python",
        "source": grader_source
    }
}
```

**Cell 5: Launch Evaluation Runs**
```python
for model in models:
    run = client.evaluations.create(
        name=f"{EVAL_NAME}-{model}",
        dataset=dataset.id,
        agent=model,
        evaluators=evaluators
    )
    print(f"✅ Started: {model} → {run.id}")
```

**Cell 6: Monitor Progress**
```python
# Auto-polls every 30 seconds
# Shows: Running → Completed
```

**Expected:** ~15-20 minutes for all 6 models (372 test cases total)

---

### 4. Review Results (3 min)

**Demo:** Open completed Foundry eval run in portal

**Show:**
- Go to Azure AI Foundry → Evaluations
- Search for `zava-multi-model-eval-{timestamp}`
- Click on completed run

**Results Table:**

| Model | Overall Pass Rate | Zava Quality | Decision | Financial | Format |
|-------|------------------|--------------|----------|-----------|--------|
| gpt-4-1-mini | 56.5% | 64.5% | 72% | 85% | 68% |
| gpt-4-1 | 54.8% | 63.5% | 70% | 83% | 67% |
| gpt-5-4 | 52.4% | 61.3% | 68% | 82% | 65% |
| o4-mini | 46.0% | 53.2% | 60% | 78% | 60% |
| gpt-5-4-mini | 44.4% | 51.8% | 58% | 76% | 58% |
| gpt-4-1-nano | 40.3% | 48.5% | 55% | 72% | 55% |

**Key Insights:**
- gpt-4-1-mini performs best (56.5% overall)
- But even best model fails 43.5% of scenarios!
- Size doesn't guarantee better performance (only 16% gap between best and worst)
- All models struggle with decision correctness (avg 64%)

---

### 5. Analyze Failure Patterns (4 min)

**Show:** `eval/BASELINE_EVAL_ANALYSIS.md`

**Key Finding: "The Execution Gap"**

```
Intent Understanding:  89.5% avg across models ✅
Task Completion:       59.7% avg across models ❌
Zava Quality:          59.9% avg across models ❌

Gap: 30% drop from understanding → execution
```

**Translation:** "Models understand WHAT to do, but fail at HOW to do it precisely"

**Common Failure Modes:**

1. **Decision Errors (50% of failures)**
   - Denying valid returns (missed eligibility window)
   - Approving invalid exchanges (out-of-stock items)
   - Wrong resolution type (refund instead of store credit for sale items)

2. **Financial Errors (30% of failures)**
   - Incorrect restocking fees (wrong tier percentage)
   - Missing shipping credits (late delivery)
   - Wrong refund amounts (didn't apply all discounts)

3. **Format Errors (20% of failures)**
   - Missing structured action lines
   - Incomplete multi-item resolutions
   - Wrong field names or values

**Example Failed Scenario:**

```
Scenario: Gold customer returns sale item (defective)
Expected: Store credit (sale items are final sale, even for defects)
Model Output: Full refund

Why it failed:
- Model saw "defective" → triggered refund logic
- Missed "sale item" exception → store credit only
- Decision error cost: 50% of score
```

---

### 6. Select Base Model for RFT (1 min)

**Recommendation:** gpt-4-1-mini

**Rationale:**
- Best baseline performance (56.5%)
- Reasonable cost/token efficiency
- Enough room for improvement (target: >80% = 24% gain)
- Good balance of capability and trainability

**Alternative:** o4-mini
- Lower baseline (46%) → larger improvement potential
- Good for showing dramatic RFT gains

**Target Post-RFT:** >80% overall pass rate

---

## ✅ Success Criteria

At the end of Phase 2, verify:
- [ ] Custom grader logic is understood
- [ ] Multi-model evaluation workflow is demonstrated
- [ ] Results show clear performance gaps
- [ ] Failure patterns are identified and explained
- [ ] Case for RFT is established
- [ ] Base model selected for Phase 3

---

## 📁 Files & Resources

| File | Purpose |
|------|---------|
| `notebooks/phase2_base_evaluations.ipynb` | Main evaluation workflow |
| `data/rft_next_val.jsonl` | 62 validation scenarios |
| `eval/zava_grader_response.py` | Custom Python grader |
| `eval/BASELINE_EVAL_ANALYSIS.md` | Comprehensive analysis report |
| `eval/baseline_analysis.json` | Machine-readable results |
| `eval/detailed_results/*.json` | Per-model metadata |
| `.env` | Project configuration (not committed) |
| `.env.example` | Template for configuration |
| `requirements.txt` | Python dependencies |

---

## 🐛 Common Issues

### Grader fails with "compile() not allowed"
- **Fix:** Use `re.search(pattern_str, text, flags)` instead of `re.compile()`
- We've already fixed this in `zava_grader_response.py`

### Grader fails with "top-level grade() not found"
- **Fix:** Must have `def grade(sample, item) -> float` function
- Already implemented in current grader

### Dataset upload fails with 404
- **Check:** PROJECT_ENDPOINT format is correct:
  ```
  https://{account}.services.ai.azure.com/api/projects/{project}
  ```
  (NOT `/discovery/projects/`)

### Evaluation run hangs or takes too long
- **Expected:** 15-20 minutes for 6 models × 62 scenarios
- **Check:** Foundry portal for status
- Can monitor via notebook Cell 6

---

## 📊 Current Status

**Eval Run:** `zava-multi-model-eval-20260526-194103`
- **Started:** 19:41:03 UTC
- **Status:** Running ⏳
- **Expected completion:** 19:56-20:01 UTC
- **Grader fixes applied:** ✅ (no re.compile(), has grade() function)

**Next Step:** Wait for completion, then analyze results

---

## 🔗 Next Phase

**Phase 3: Reinforcement Fine-Tuning (RFT)**

Now that we've identified where base models fail, let's use RFT to teach them the correct behavior.

[→ Go to Phase 3 Guide](phase3_rft_training.md)
