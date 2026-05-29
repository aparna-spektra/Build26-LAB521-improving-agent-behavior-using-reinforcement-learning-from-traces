# Part 5 — Training Results & Evaluate the Fine-Tuned Model

> [!NOTE]
> **Notebook**: `src/05-training-results-evaluate.ipynb` | **Estimated time**: ~15 minutes

In this section, you'll analyze the training reward curve from a completed RFT run, compare checkpoints, and run a head-to-head evaluation of the fine-tuned model against the base model.

> [!TIP]
> Your submitted job from notebook 04 can take 10 hours to complete. This notebook uses **a model we already trained for you** from an identical experiment so you can see the full training story without waiting. Once your job finishes, you can re-run this notebook with your own results.

## Step 1: Open the Notebook

> [!TIP]
> As you open a new notebook, first, click on notebook file to open it. Next, at the top of the notebook click the **Run All** command to execute the notebook. A pop up will be created, select: **Python 3.13....**, you will have successfully executed the notebook.

1. Open **`src/05-training-results-evaluate.ipynb`** in VS Code.
1. You will need to add the credentials of an already finetuned model, the credentials are as follows:
     -  azure_endpoint: endpoint variable
     - api_key: key variable
1. Run the **Setup** cell to reconnect to Microsoft Foundry and reload the agent infrastructure.

## Step 2: Plot the Reward Curve

Run the **Plot Reward Curve** cell. This loads pre-computed training metrics from `results/training_metrics.csv` and plots:

- **Train and validation reward** — average grader score on training examples and held-out validation examples per step
- **Completion and reasoning tokens** - how many completion and reasoning tokens the model was using on each request, showing how hard the model is thinking
- **Tool call errors** — how often the model failed to call `get_order` correctly

### What a healthy reward curve looks like

| Signal | What to look for |
|--------|-----------------|
| Train reward | Rises steadily, then plateaus |
| Validation reward | Tracks train reward — large divergence suggests overfitting |
| Tokens | Rises steadily as the model improves its thinking strategies |
| Tool call errors | Should drop sharply in early steps as the model learns to call `get_order` |

> [!TIP]
> The **best checkpoint** is not always the last one. The train or validation reward may peak at an intermediate step and then slightly decline as the model overfits to the training distribution. Always evaluate multiple checkpoints on your held-out data.

## Step 3: Compare Checkpoints

Run the **Checkpoint Comparison** cell. This contains evaluation scores for checkpoints at steps 95 and 115.

You'll see something like:

| Checkpoint | Avg Score | P@0.8 (pass rate) |
|------------|-----------|-------------------|
| Base o4-mini | ~0.73 | ~60% |
| Step 95 | ~0.93 | ~80% |
| Step 115 | ~0.96 | ~90% |

> [!NOTE]
> **Step 115 outperforms Step 95** even though the training log shows Step 95 with a slightly higher train reward in some experiments. This is a common RFT pattern: training-time metrics use a sample of rollouts, while held-out evaluation on the full validation set gives a more reliable signal. **Always re-evaluate checkpoints on full held-out data before choosing the best one.**

## Step 4: Run the Head-to-Head Evaluation

Run the **Head-to-Head Evaluation** cells. This runs the same 8 validation scenarios on both:
- **Base `o4-mini`** — the unmodified model
- **`o4-mini-2025`** — the best fine-tuned checkpoint, pre-deployed by your facilitator

> [!WARNING]
> This cell makes ~16 API calls and takes approximately **8–12 minutes**. The notebook uses concurrent requests where possible to speed this up.

### What to look for in the results

For each scenario, you'll see the raw responses and grader scores side by side. Pay attention to:

- **Edge cases**: Does the fine-tuned model correctly handle defective sale items (store credit, not refund)?
- **Amount accuracy**: Are the dollar figures exact, or does the model round incorrectly?
- **Policy citations**: Does the fine-tuned model cite more specific policy rules?
- **Tool calling**: Does the fine-tuned model always call `get_order` before answering?

### Expected results

  Average score                 69.5%          96.0%    +26.5%
  Pass@0.9 (strict)               12%            88%      +75%
  Pass@0.8 (good)                 50%           100%      +50%

| Metric | Base o4-mini | Fine-tuned (Step 115) |
|--------|-------------|----------------------|
| Average score | ~73% | **~96%** |
| Pass rate (P@0.8) | ~60% | **~100%** |
| Tool call error rate | ~28% | **~7%** |

## Key Takeaways

- **RFT improved average score from ~73% to ~96%** — a significant gain on policy-following accuracy
- **The reward curve confirms learning** — train and validation reward both rise, and tool call errors drop sharply
- **Step 115 beats Step 95** for this task — always evaluate checkpoints on full held-out data, not just training metrics
- **P@0.8 jumped from 60% → 100%** — the fine-tuned model now passes the "good" bar on 10 out of 10 scenarios
- **The model didn't need labeled responses** — it discovered correct behavior entirely through trial and error

Click **Next** to wrap up and explore next steps.
