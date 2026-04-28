# Agentic RFT Lessons Learned

Hard-won lessons from building an agentic RFT pipeline for a Zava retail tool-calling task on Azure AI Foundry.

## 1. Always Baseline Before Training

**Run your exact grader against the base model before submitting any RFT job.** Check:
- Average score across your training/validation set
- Pass rate at your chosen threshold
- Score distribution (are scores clustered or spread?)

Target: **30-50% of base model rollouts should FAIL** at your threshold. If pass rate is >90%, the threshold is too lenient (no learning signal). If <10%, it's too strict (sparse reward).

## 2. The Eval Framework Does NOT Execute Tools

During agentic RFT, **training rollouts** correctly call your tool endpoints and get results. But the **validation evals** (the metrics shown in Foundry UI) do NOT execute the tool loop. The eval captures only the model's first response — which is typically a tool call with empty text content.

**Impact:**
- `valid_reward_mean` will be misleadingly low (~0)
- Eval pass rates in the UI will show ~0% even when training is working
- Checkpoint selection (which uses `valid_reward_mean`) may pick suboptimal checkpoints

**Workaround:** Ignore the UI eval metrics. Monitor `train_mean_reward` instead. After training, evaluate checkpoints yourself using a local harness that executes the full tool loop.

## 3. Grader Selection Matters Enormously

We tested 4 grader types. Key findings:

| Grader Type | Pros | Cons | Recommendation |
|------------|------|------|----------------|
| **Python grader** | Fast, deterministic, can access `output_tools` | Can't execute tools or call APIs | Best for scoring final text + tool call metadata |
| **Multi grader** | Built-in, no HTTP. `score_model` gives nuanced scores | score_model adds latency/cost per rollout | Good for semantic quality scoring |
| **Endpoint grader** | Full control, can run arbitrary logic | HTTP reliability issues (timeouts, errors). ~500 errors/step in our case | Use only if you need server-side logic |
| **String check** | Simplest, most reliable | Binary 0/1 only, no partial credit | Good for exact-match tasks (not ours) |

**Our recommendation:** For agentic (tool-calling) tasks, prefer an **endpoint grader** — it receives the full trace including tool call results, so it can verify the model used tool data correctly, not just that it called the right tool. Build it robustly (try/except everything, always return `{"score": float}`). Use a **Python grader** for simpler tasks where `sample.output_text` and `sample.output_tools` metadata are sufficient. Use **multi grader** with `score_model` when you need semantic similarity judgment without running your own endpoint.

## 4. Grader Errors are Silent Killers

Our endpoint grader returned ~500 errors per training step, but the job "succeeded" — it just learned nothing. The `grader_train` score was 0 for all 20 steps.

**How to detect:** Check the training metrics CSV after completion. Look for:
- `errors/graders/.../train_other_error_count` — should be 0 or very low
- `scores/graders/.../train_reward_mean` — should be non-zero
- If `train_mean_reward` is always negative and `grader_train` is 0, your grader is broken

## 5. Partial Credit is Critical

Binary pass/fail graders (score 0 or 1) give sparse reward — most rollouts get 0. The model needs **partial credit** to learn incrementally:
- Correct action but wrong amount → 0.4 (not 0)
- Right tool called but wrong final answer → 0.1 (not 0)
- Close but not exact → 0.5-0.8 (not 0)

Our Python grader v2 scores across 4 dimensions: action correctness (0.4), amount accuracy (0.3), policy reasoning (0.2), tool usage (0.1).

## 6. pass_threshold Controls the Reward Signal

`pass_threshold` determines what score counts as "pass" vs "fail" for the RL reward signal. The relationship between threshold and pass rate is non-obvious:

| pass_threshold | Base model pass rate | Learning signal |
|---------------|---------------------|-----------------|
| 0.5 | ~100% | ❌ No signal (everything passes) |
| 0.7 | ~75% | ⚠️ Weak signal |
| 0.9 | ~67% | ✅ Good signal (~33% fail) |
| 0.95 | ~60% | ✅ Good signal (~40% fail) |
| 1.0 | ~33% | ⚠️ May be too strict |

**Calibrate empirically:** Run your grader on 15-30 base model outputs and compute pass rates at different thresholds before submitting.

## 7. RFT Training Data Format (with tools)

For agentic RFT with tool calling:
```json
{
  "messages": [
    {"role": "developer", "content": "system prompt with policy rules"},
    {"role": "user", "content": "customer request"}
  ],
  "expected_resolution": "the correct answer for grading"
}
```

- Use `developer` role (not `system`) — RFT does not support `system` messages
- The last message must be `user` or `developer` role
- Extra fields (`expected_resolution`, etc.) are accessible in the grader via `item.field_name`
- Tool schemas go in the job config `tools` parameter, NOT in the training data

## 8. Tool Endpoints Need to Handle Load

RFT training sends parallel rollouts to your tool endpoints. Requirements:
- **~50 QPS recommended** (actual load depends on compute_multiplier and parallelism)
- **Timeouts**: Platform waits up to 10 minutes per tool call
- **Errors**: 5xx errors → platform retries 3x then discards the rollout
- **Payload format**: Receives `{"type": "function_call", "arguments": "{...}", "call_id": "...", "trace_id": "..."}`
- **Response format**: Must return `{"type": "function_call_output", "call_id": "...", "output": "..."}`

We used Azure App Service (B1 tier, 4 workers) — handles ~5 QPS which was sufficient for our 60-example dataset.

## 9. Monitor Training Metrics, Not Eval Metrics

The key metric is `train_mean_reward`:
- **Positive and increasing** → model is learning ✅
- **Negative throughout** → grader/threshold issue, model not getting reward
- **Starts positive, goes negative** → possible reward hacking or overfitting
- **Flat at ~0** → grader is erroring or threshold is too strict

Download the results CSV after training to check:
- `train_mean_reward` per step
- `grader_error_count` — should be ~0
- `tool_calls_to_*` — monitor if model stops calling tools over training
- `completion_tokens_mean` — watch for output length changes

## 10. Start Small and Iterate

Our iteration path:
1. 20 examples, compute_multiplier=1.0, 1 epoch → barely any signal
2. 60 examples, compute_multiplier=1.5, 2 epochs → first positive reward
3. 200 examples (next) → expecting stronger improvement

RFT best practices suggest 10-100 examples to validate the setup, then scale up. Don't invest in a large dataset until you've confirmed the grader works and rewards are positive.

## 11. o4-mini is Already Very Good

The hardest part of our experiment was finding a task where o4-mini genuinely struggles. Policy resolution with all details in the prompt: 94.5%. With tools that compute the answer: 88%. Even with raw-data tools requiring the model to reason: 70%.

For a lab/demo, SFT distillation (nano: 61% → 73.5%) showed clearer improvement than RFT on o4-mini. RFT shines when the base model has significant room to improve (40-70% baseline).

## 12. Grading Tool Calls Directly

Per the [OpenAI docs](https://developers.openai.com/api/docs/guides/graders#limitations-and-tips), you can grade tool calls using `sample.output_tools`:

```json
{
  "type": "multi",
  "graders": {
    "function_name": {
      "type": "string_check",
      "input": "expected_tool_name",
      "reference": "{{sample.output_tools[0].function.name}}",
      "operation": "eq"
    },
    "arguments": {
      "type": "text_similarity",
      "input": "{\"order_id\": \"{{item.expected_order_id}}\"}",
      "reference": "{{sample.output_tools[0].function.arguments}}",
      "evaluation_metric": "fuzzy_match"
    }
  },
  "calculate_output": "0.5 * function_name + 0.5 * arguments"
}
```

This avoids the endpoint grader entirely and grades tool calls deterministically. Use `text_similarity` over `string_check` for arguments to handle minor formatting differences.