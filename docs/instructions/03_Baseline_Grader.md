# Part 3 — Baseline Evaluation & The Grader

> [!NOTE]
> **Notebook**: `src/03-baseline-grader.ipynb` | **Estimated time**: ~15 minutes

In this section, you'll measure how well the base model performs on Zava's return scenarios, understand the grader that drives RFT learning, and calibrate the pass threshold for optimal training signal.

## Step 1: Open the Notebook

> [!TIP]
> As you open a new notebook, first, click on notebook file to open it. Next, at the top of the notebook click the **Run All** command to execute the notebook. A pop up will be created, select: **Python 3.13....**, you will have successfully executed the notebook.

1. Open **`src/03-baseline-grader.ipynb`** in VS Code.
2. Run the **Setup** cell to reconnect to Microsoft Foundry and reload the agent infrastructure.

## Step 2: Understand the Grader

The grader is the most important concept in RFT. It replaces the "ideal assistant response" used in supervised fine-tuning with a **scoring function** that evaluates model outputs.

Run the **Define the Grader** cell to load the grader function.

The grader scores each response on four dimensions:

| Dimension | Weight | How it's evaluated |
|-----------|--------|-------------------|
| **Correct action** | 40% | Keyword match for refund / denial / store credit / exchange |
| **Correct amounts** | 30% | Dollar figures extracted and compared with tolerance |
| **Policy reasoning** | 20% | Checks for citation of applicable policy rules |
| **Tool usage** | 10% | Verifies the agent called `get_order` |

The grader returns a float in `[0.0, 1.0]`. A response that gets the action right and cites policy earns ~60% even if the dollar amounts are off.

> [!TIP]
> **Why partial credit?** Binary scoring (pass/fail) provides a weak training signal — the model can't tell whether it was "almost right" or completely wrong. Partial credit scoring lets the RL algorithm distinguish between near-misses and total failures, leading to faster and more stable learning.

### RFT vs. SFT

| | Supervised Fine-Tuning (SFT) | Reinforcement Fine-Tuning (RFT) |
|---|---|---|
| Training data | Prompt + ideal response pairs | Prompts only + grader function |
| Signal | "Copy this response" | "This attempt scored 0.85 — do better" |
| Best for | Teaching format and style | Improving reasoning and accuracy |
| Data required | Labeled examples | Diverse prompts + a good grader |

## Step 3: Load the Validation Scenarios

Run the **Load Validation Scenarios** cell to load the 57 held-out scenarios from `data/rft_v7_val.jsonl`.

These scenarios cover all major policy rules and edge cases in the Zava return policy. They are **never** used as training data — only for evaluation.

> [!NOTE]
> The next cell demonstrates generating ground-truth answers by running our 57 validation scenarios through the trusted `gpt-5.4` model and caching the results to `data/rft_v7_val_gt.jsonl`. This takes ~15–20 minutes for all scenarios. If the cache file already exists, it loads instantly.

## Step 4: Run the Baseline Evaluation

Run the **Run the Baseline Evaluation** cell. This samples **8 scenarios** from the validation set and runs the full agent loop on each one, scoring the result with the grader.

> [!WARNING]
> This cell makes ~8 API calls and takes approximately **5–8 minutes**. While it runs, move on to reading the grader explanation in the notebook and the threshold calibration section below.

### What to expect

The base `o4-mini` model typically scores around **0.73 average** on Zava's validation set. You'll see a mix of:
- High scores (0.9–1.0) on straightforward cases
- Medium scores (0.5–0.7) on edge cases where the model gets the action right but amounts wrong
- Low scores (0.0–0.3) on complex policy interactions (e.g., defective sale items)

## Step 5: Calibrate the Pass Threshold

The **pass threshold** determines what counts as "success" during RFT training. Run the **Calibrate the Pass Threshold** cell.

The goal is a **30–50% failure rate** on the baseline model:

| Failure rate | Implication |
|---|---|
| < 20% | Model already passes most examples — little to learn from |
| 30–50% | **Ideal range** — strong learning signal without sparse reward |
| > 60% | Too hard — sparse rewards make convergence slow |

A threshold of **0.80** typically gives a ~35% failure rate on base `o4-mini`, making it the default for this lab.

> [!TIP]
> The pass threshold is a hyperparameter you can tune. A higher threshold (e.g., 0.90) pushes the model harder but converges more slowly. For this lab, use the default of 0.80.

## Key Takeaways

- Base `o4-mini` scores **~73%** on Zava policy scenarios — good, but with room to improve
- The grader provides **partial credit** (0.0–1.0) rather than binary pass/fail, enabling richer training signal
- A **pass threshold of 0.80** gives an optimal ~35% failure rate for RL learning
- RFT uses these scores to teach the model which behaviors to reinforce through trial and error

Click **Next** to build training data and submit a real RFT job.
