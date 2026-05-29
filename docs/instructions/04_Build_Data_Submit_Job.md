# Part 4 — Build Training Data & Submit a Job

> [!NOTE]
> **Notebook**: `src/04-build-data-submit-job.ipynb` | **Estimated time**: ~15 minutes

In this section, you'll explore the RFT training data format, construct a custom training example from scratch, and submit a real fine-tuning job to Microsoft Foundry.

## Step 1: Open the Notebook

> [!TIP]
> As you open a new notebook, first, click on notebook file to open it. Next, at the top of the notebook click the **Run All** command to execute the notebook. A pop up will be created, select: **Python 3.13....**, you will have successfully executed the notebook.

1. Open **`src/04-build-data-submit-job.ipynb`** in VS Code.
2. Run the **Setup** cell to reconnect to Microsoft Foundry and reload the agent infrastructure.

## Step 2: Explore the RFT Data Format

Run the **Explore the Data Format** cell to examine a training example from `data/rft_v7_train.jsonl`.

RFT training data is intentionally simpler than SFT data — you only need **user prompts**, not assistant responses:

```json
{
  "messages": [
    {"role": "developer", "content": "<system prompt with Zava policy>"},
    {"role": "user", "content": "I want to return the drill I bought last week..."}
  ],
  "expected_resolution": {
    "action": "refund",
    "amount": 45.50,
    "reason": "within_return_window"
  }
}
```

> [!TIP]
> The `expected_resolution` field is **only used by the grader** to score model outputs during training. You don't provide model responses — the model generates those itself during training rollouts.

Run the **Dataset Overview** cell to see how many training and validation examples are in the pre-built dataset.

### How the training data was built

The pre-built dataset (`rft_v7_train.jsonl`, 343 examples) was constructed in two steps:
1. ~40 unique scenarios were written by hand, covering every policy rule and edge case
2. An LLM generated 10 rephrasings of each scenario (different tones, wordings, levels of detail), creating 400 diverse examples

This approach ensures the model encounters the same underlying policy rules across many different customer phrasings — which is critical for generalization.

## Step 3: Build Your Own Training Example

Run the **Build Your Own Example** section. This is an interactive exercise:

1. Call the `get_order` tool on a sample order ID to see what data is available
2. Determine the correct resolution based on the Zava return policy
3. Write the `expected_resolution` object with the correct action, amount, and reason
4. Run the grader on your example to verify it scores correctly

> [!TIP]
> This exercise builds intuition for what makes a good RFT training example. The key insight: **data diversity matters more than volume**. A dataset with 50 truly diverse scenarios often outperforms one with 500 near-identical paraphrases.

## Step 4: Upload Files

Run the **Upload Files** cell to upload the pre-built training and validation datasets to Microsoft Foundry.

The cell will return file IDs for both files. These IDs are used in the subsequent job submission step.

> [!NOTE]
> File processing takes **10–30 seconds** after upload. The notebook includes a wait loop that polls the file status. Wait for both files to show `processed` before proceeding.

## Step 5: Define the Grader for the Training Job

Run the **Define the Grader** cell. This embeds the same Python grader function you used for local evaluation as a string — the Microsoft Foundry training service executes this grader on each model rollout during training.

The grader string must define a `grade(sample, item)` function:
- `sample` — the training example (contains `expected_resolution`)
- `item` — the model's output for that rollout
- Returns a float in `[0.0, 1.0]`

## Step 6: Submit the RFT Job

Run the **Submit the Job** cell to submit your fine-tuning job. The job is configured with:

| Parameter | Value | Why |
|-----------|-------|-----|
| Base model | `o4-mini` | Capable reasoning model with tool-calling support |
| Pass threshold | `0.80` | Gives ~35% failure rate — optimal learning signal |
| Epochs | `3` | Sufficient for convergence on a 343-example dataset |
| Reasoning effort | `medium` | Balances training cost and quality |
| Checkpoint interval | Every 5 steps | Lets you compare intermediate checkpoints |

The cell will print your **job ID**. Save it — you'll use it in notebook 05 to check status and in notebook 06 to review your results.

> [!WARNING]
> RFT jobs are queued and run sequentially per resource. If multiple participants submit at the same time, your job may show `queued` status — this is expected. Jobs typically complete in **10 hours**.

We already submitted an RFT job in Microsoft Foundry, to see the job submitted, go to:

1. Go back to browser where you logged in to **Microsoft Foundry** using <[https://ai.azure.com/nextgen](https://ai.azure.com/nextgen). Close all the pop ups.
1. Switch to **New Foundry** by toggling the switch button on the top right if it is not already toggled.
1. In the new window, on the top right navigation, select **Build**
1. On the right side bar, select **Fine Tune**, you will see the jobs you submitted and one previously submitted. Some jobs might actually have been started already, click on the link to the fine tuning job to view any results or outcomes.

> [!TIP]
> Good News though, you don't need to wait for your job to finish to continue with the lab. Notebook 05 uses **pre-run results** from a completed experiment to demonstrate what the reward curve and checkpoint evaluation look like. And we have an already fine tuned model you can test out

## Key Takeaways

- RFT training data only needs **prompts + expected answers** — no ideal assistant responses
- **Data diversity** matters more than volume: diverse scenarios generalize better than large paraphrase sets
- The grader embedded in the job definition is the **same function** used for local evaluation — consistency is critical
- Jobs are queued; results arrive in **10 hours** — you'll evaluate pre-run results in the next notebook

Click **Next** to explore training results and evaluate the fine-tuned model.
