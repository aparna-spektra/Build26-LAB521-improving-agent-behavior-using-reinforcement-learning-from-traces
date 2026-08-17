# Lab: Lab Notebook

## 📘 Lab Scenario
In this lab, you will work through the notebook src\reference files\lab-notebook.ipynb and execute each code cell in sequence to complete the workflow successfully.

## 📖 Overview
This instruction file mirrors the notebook execution order. Each section includes the exact code from a code cell, what it does, any pre-run action, and the expected result.

## 🎯 Objectives
- Execute every code cell in the notebook in the correct order
- Understand what each cell configures or runs
- Validate expected outputs before moving to the next cell

## Task 1: Execute Notebook Code Cells

1. Open the corresponding notebook and ensure the correct kernel/session is attached before running any code cells.
2. Run cells one-by-one in the exact order listed below.

### Code Cell 1

1. Run the below cell.

```python
# Install dependencies (uncomment if needed)
# %pip install -q openai python-dotenv requests tabulate matplotlib
```
**What this code does:**
Installs notebook dependencies required by later cells.

**Before you run this cell:**
Ensure required environment variables, credentials, and files are available before running this first cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 2

1. Run the below cell.

```python
import json, os, re, time, textwrap
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

# Quick connectivity check — make a simple chat completion
test = client.chat.completions.create(
    model="o4-mini",
    messages=[{"role": "user", "content": "Say 'hello' in one word."}],
)
print(f"✅ Connected! Model responded: {test.choices[0].message.content}")
```
**What this code does:**
Authenticates and configures service clients used throughout the lab.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 3

1. Run the below cell.

```python
pip install fastapi
```
**What this code does:**
Installs notebook dependencies required by later cells.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 4

1. Run the below cell.

```python
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "function_app"))
from function_app import get_order as _get_order_local

# === Tool endpoint (pre-deployed Azure Function) ===
TOOL_URL = "https://zava-rft-tools.azurewebsites.net"

# The system prompt the agent uses
SYSTEM_PROMPT = """You are Zava's return resolution engine. Call get_order to look up order details, then apply the return policy to compute the resolution.

POLICY: Standard=30d/15d(electronics), Gold=45d/30d, Platinum=60d/45d. Electronics restocking: Std=15%, Gold=7.5%, Plat=0%. Defective=0%. Sale=final sale (defective sale→store credit). Late delivery(>2d)=$10 credit +15d extension. Lost=replacement/refund. Pending=cancellable. Opened personal care=deny unless defective.

Respond with your resolution including: action, amounts, and policy reasoning."""

# Tool definition (same schema the model sees)
TOOLS = [
    {"type": "function", "function": {
        "name": "get_order",
        "description": "Look up order details including items, prices, dates, loyalty tier, and delivery status.",
        "parameters": {"type": "object", "properties": {
            "order_id": {"type": "string", "description": "The order ID (e.g., ORD-003)"}
        }, "required": ["order_id"]}
    }}
]


def call_tool(name, args):
    """Call the Zava tool endpoint, falling back to local implementation if unavailable."""
    if name == "get_order":
        try:
            url = f"{TOOL_URL}/tool/{name}"
            payload = {"arguments": json.dumps(args), "call_id": "c", "id": "f", "trace_id": "t"}
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200:
                return r.json().get("output", json.dumps(r.json()))
        except Exception:
            pass
        # Fallback: call local implementation directly
        return _get_order_local(args["order_id"])
    return json.dumps({"error": f"Unknown tool: {name}"})


def run_agent(user_message, model="gpt-5-mini", verbose=True):
    """Run the full agent loop: model → tool call → model → response."""
    messages = [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    tool_calls_made = []

    for turn in range(8):  # max 8 turns to prevent infinite loops
        resp = client.chat.completions.create(
            model=model, messages=messages, tools=TOOLS, max_completion_tokens=8192
        )
        msg = resp.choices[0].message

        # Build assistant message for conversation history
        assistant_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
            tool_calls_made.extend(msg.tool_calls)
        messages.append(assistant_msg)

        # If no tool calls, we're done
        if not msg.tool_calls:
            if verbose and msg.content:
                print(f"\n📋 Agent Response:\n{textwrap.fill(msg.content, width=80)}")
            return msg.content or "", tool_calls_made

        # Execute tool calls
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            if verbose:
                print(f"  🔧 Calling {tc.function.name}({args})")
            result = call_tool(tc.function.name, args)
            if verbose:
                # Show a preview of the tool result
                preview = result[:200] + "..." if len(result) > 200 else result
                print(f"  📦 Result: {preview}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return "", tool_calls_made
```
**What this code does:**
Imports required Python libraries and prepares the runtime environment.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 5

1. Run the below cell.

```python
# Scenario 1: Defective electronics return (should be easy)
print("=" * 60)
print("SCENARIO 1: Defective headphones")
print("=" * 60)
response, tools = run_agent(
    "Hi, I'm Ava Chen. The headphones from ORD-002 have a cracked speaker. I want a refund."
)
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 6

1. Run the below cell.

```python
# Scenario 2: Complex — sale item + defective (tricky policy interaction)
print("=" * 60)
print("SCENARIO 2: Defective sale item")
print("=" * 60)
response, tools = run_agent(
    "Emma Kim. The face serum from ORD-004 caused a skin reaction. It was on sale but it's defective."
)
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 7

1. Run the below cell.

```python
# Scenario 3: Exchange request (the model often struggles with these)
print("=" * 60)
print("SCENARIO 3: Exchange request")
print("=" * 60)
response, tools = run_agent(
    "Noah Brown. Exchange hiking boots from ORD-010 for size 11."
)
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 8

1. Run the below cell.

```python
def python_grader(output_text, output_tools, expected_resolution):
    """Score a model response against the expected resolution.
    Returns 0.0 to 1.0 — same logic used during RFT training."""
    if not expected_resolution:
        return 0.5

    score = 0.0
    exp_lower = expected_resolution.lower()
    out_lower = (output_text or "").lower()

    # Action correctness (0.4)
    actions = {
        "refund": ["refund"],
        "denied": ["denied", "deny", "not eligible", "cannot", "expired"],
        "store credit": ["store credit", "store_credit"],
        "replacement": ["replacement", "replace"],
        "exchange": ["exchange", "swap"],
        "cancel": ["cancel", "cancellation"],
    }
    for action, keywords in actions.items():
        if any(k in exp_lower for k in keywords):
            if any(k in out_lower for k in keywords):
                score += 0.4
            break

    # Amount correctness (0.3)
    exp_amounts = re.findall(r'\$(\d+\.\d{2})', expected_resolution)
    if exp_amounts:
        out_amounts = re.findall(r'\$(\d+\.\d{2})', output_text or "")
        hits = sum(1 for a in exp_amounts if a in out_amounts)
        score += 0.3 * (hits / len(exp_amounts))
    else:
        score += 0.15

    # Policy reasoning (0.2)
    policy_terms = ["window", "restocking", "defective", "sale", "platinum", "gold",
                    "standard", "late", "shipping credit", "personal care", "eligible"]
    exp_terms = [t for t in policy_terms if t in exp_lower]
    if exp_terms:
        hits = sum(1 for t in exp_terms if t in out_lower)
        score += 0.2 * (hits / len(exp_terms))

    # Tool usage bonus (0.1)
    if output_tools:
        tool_names = [t.function.name if hasattr(t, 'function') else t.get("function", {}).get("name", "") for t in output_tools]
        if "get_order" in tool_names:
            score += 0.1

    return round(min(score, 1.0), 3)
```
**What this code does:**
Defines reusable helper logic that later cells execute.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 9

1. Run the below cell.

```python
# Load validation scenarios
with open("data/rft_v7_val.jsonl") as f:
    val_scenarios = [json.loads(line) for line in f]

print(f"Loaded {len(val_scenarios)} validation scenarios")
print(f"Sample: {val_scenarios[0]['messages'][-1]['content']}")
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 10

1. Run the below cell.

```python
# Run baseline evaluation (takes ~5-8 minutes with 8 scenarios)
import random
random.seed(42)
eval_scenarios = random.sample(val_scenarios, min(8, len(val_scenarios)))

print(f"Evaluating base o4-mini on {len(eval_scenarios)} scenarios...\n")
base_scores = []

for i, ex in enumerate(eval_scenarios):
    msg = ex["messages"][-1]["content"]
    expected = ex.get("expected_resolution", "")

    output, tools = run_agent(msg, model="o4-mini", verbose=False)
    score = python_grader(output, tools, expected)
    base_scores.append(score)

    status = "✅" if score >= 0.9 else ("⚠️" if score >= 0.5 else "❌")
    print(f"  [{i+1:2d}] {score:.3f} {status}  {msg}")

base_avg = sum(base_scores) / len(base_scores)
base_p90 = sum(1 for s in base_scores if s >= 0.9) / len(base_scores)
base_p80 = sum(1 for s in base_scores if s >= 0.8) / len(base_scores)

print(f"\n{'='*50}")
print(f"  BASE o4-mini RESULTS")
print(f"  Average score: {base_avg:.1%}")
print(f"  Pass@0.9 (strict): {base_p90:.0%}")
print(f"  Pass@0.8 (good): {base_p80:.0%}")
print(f"{'='*50}")
```
**What this code does:**
Retrieves job status or evaluates model/checkpoint performance.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 11

1. Run the below cell.

```python
# Calibration: what threshold gives the right failure rate?
print("Pass threshold calibration (base o4-mini):\n")
print(f"  {'Threshold':>10} {'Pass Rate':>10} {'Fail Rate':>10} {'Signal Quality':>15}")
print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*15}")

for threshold in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]:
    pass_rate = sum(1 for s in base_scores if s >= threshold) / len(base_scores)
    fail_rate = 1 - pass_rate
    quality = "✅ Good (25-50%)" if 0.25 <= fail_rate <= 0.50 else ("⚠️ Too easy" if fail_rate < 0.25 else "⚠️ Too hard")
    print(f"  {threshold:>10.2f} {pass_rate:>9.0%} {fail_rate:>9.0%} {quality:>15}")

print(f"\n💡 We use pass_threshold=0.80 → ~35% failure rate → good learning signal")
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 12

1. Run the below cell.

```python
# Let's look at the data format
sample = json.loads(open("data/rft_v7_train.jsonl").readline())
print("Training example format:")
print(json.dumps(sample, indent=2)[:600])
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 13

1. Run the below cell.

```python
# Look up an order to understand the data
order_data = call_tool("get_order", {"order_id": "ORD-003"})
print("Order ORD-003 data:")
print(json.dumps(json.loads(order_data), indent=2))
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 14

1. Run the below cell.

```python
# Now write a training example. ORD-003 belongs to Yusuf Rossi (Gold tier).
# Think: what's a realistic customer request? What's the correct policy resolution?

my_example = {
    "messages": [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Yusuf Rossi here. The keyboard from ORD-003 stopped working after a week. Keys are unresponsive."}
    ],
    "expected_resolution": "Refund $89.99 for defective keyboard. Gold tier, within 45-day window. Defective items have $0 restocking fee."
}

# Test: what does base o4-mini say for our example?
output, tools = run_agent(my_example["messages"][-1]["content"], verbose=True)
score = python_grader(output, tools, my_example["expected_resolution"])
print(f"\n🎯 Grader score: {score:.3f}")
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 15

1. Run the below cell.

```python
# Step 2: Upload files
print("Uploading training data...")
with open("data/rft_v7_train.jsonl", "rb") as f:
    train_file = client.files.create(file=f, purpose="fine-tune")
print(f"  Train: {train_file.id} ({train_file.bytes:,} bytes)")

with open("data/rft_v7_val.jsonl", "rb") as f:
    val_file = client.files.create(file=f, purpose="fine-tune")
print(f"  Val: {val_file.id} ({val_file.bytes:,} bytes)")

# Wait for processing
import time
for _ in range(12):
    t = client.files.retrieve(train_file.id)
    v = client.files.retrieve(val_file.id)
    if t.status == "processed" and v.status == "processed":
        print("  ✅ Files ready!")
        break
    time.sleep(10)
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
File IDs and status transitions ending in a processed or ready state.

### Code Cell 16

1. Run the below cell.

```python
# Step 3: Define the grader (same Python function, embedded as a string)
GRADER_SOURCE = r"""
import json
import re

def grade(sample, item):
    output_text = sample.get("output_text", "") or ""
    output_tools = sample.get("output_tools", []) or []
    expected = item.get("expected_resolution", "")
    if not expected:
        return 0.5
    score = 0.0
    exp_lower = expected.lower()
    out_lower = output_text.lower()

    # Action (0.4)
    actions = {"refund": ["refund"], "denied": ["denied", "deny", "not eligible", "cannot", "expired"],
        "store credit": ["store credit", "store_credit"], "replacement": ["replacement", "replace"],
        "exchange": ["exchange", "swap"], "cancel": ["cancel", "cancellation"]}
    for action, keywords in actions.items():
        if any(k in exp_lower for k in keywords):
            if any(k in out_lower for k in keywords):
                score += 0.4
            break

    # Amount (0.3)
    exp_amounts = re.findall(r'\$(\d+\.\d{2})', expected)
    if exp_amounts:
        out_amounts = re.findall(r'\$(\d+\.\d{2})', output_text)
        hits = sum(1 for a in exp_amounts if a in out_amounts)
        score += 0.3 * (hits / len(exp_amounts))
    else:
        score += 0.15

    # Policy terms (0.2)
    policy_terms = ["window", "restocking", "defective", "sale", "platinum", "gold",
                    "standard", "late", "shipping credit", "personal care", "eligible"]
    exp_terms = [t for t in policy_terms if t in exp_lower]
    if exp_terms:
        hits = sum(1 for t in exp_terms if t in out_lower)
        score += 0.2 * (hits / len(exp_terms))

    # Tool usage (0.1)
    if output_tools:
        tool_names = [t.get("function", {}).get("name", "") for t in output_tools]
        if "get_order" in tool_names:
            score += 0.1

    return round(min(score, 1.0), 3)
"""
```
**What this code does:**
Defines reusable helper logic that later cells execute.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 17

1. Run the below cell.

```python
# Step 4: Submit the job!
TOOL_CONFIG = [
    {"name": "get_order",
     "server_url": f"{TOOL_URL}/tool/get_order",
     "headers": {}}
]

job = client.fine_tuning.jobs.create(
    model="o4-mini",
    training_file=train_file.id,
    validation_file=val_file.id,
    suffix="zava-lab",
    method={"type": "reinforcement", "reinforcement": {
        "grader": {
            "type": "python",
            "name": "zava_grader",
            "source": GRADER_SOURCE.strip(),
            "pass_threshold": 0.80,        # <-- 35% fail rate = good signal
        },
        "tools": TOOL_CONFIG,
        "max_episode_steps": 5,
        "hyperparameters": {
            "n_epochs": 3,
            "learning_rate_multiplier": 1.0,
            "compute_multiplier": 1.5,
            "reasoning_effort": "medium",
            "eval_interval": 5,
            "eval_samples": 10,
        },
    }},
)

print(f"🚀 Job submitted!")
print(f"   ID: {job.id}")
print(f"   Status: {job.status}")
print(f"   Model: {job.model}")
print(f"\n⏳ Training takes ~2-4 hours. We'll explore pre-run results next.")
```
**What this code does:**
Submits a fine-tuning job with the configured model, grader, and hyperparameters.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
A job ID and initial job status such as pending or queued. If validation fails, an API error message is returned.

### Code Cell 18

1. Run the below cell.

```python
import csv
import matplotlib.pyplot as plt

# Load pre-run training metrics
with open("results/v5_py90_training_metrics.csv") as f:
    metrics = list(csv.DictReader(f))

steps = [int(r["step"]) for r in metrics]
train_rewards = [float(r["train_mean_reward"]) for r in metrics]
valid_rewards = [float(r["full_valid_mean_reward"]) if r.get("full_valid_mean_reward") else None for r in metrics]
comp_tokens = [float(r["completion_tokens_mean"]) for r in metrics]

# Plot reward curve
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Reward trajectory
ax = axes[0][0]
ax.plot(steps, train_rewards, "b-o", label="Train reward", markersize=4)
valid_steps = [s for s, v in zip(steps, valid_rewards) if v is not None]
valid_vals = [v for v in valid_rewards if v is not None]
ax.plot(valid_steps, valid_vals, "r-s", label="Validation reward", markersize=6)
ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
ax.set_xlabel("Training Step")
ax.set_ylabel("Mean Reward")
ax.set_title("📈 Reward Trajectory — Is the model learning?")
ax.legend()
ax.grid(True, alpha=0.3)

# 2. Completion tokens (response length)
ax = axes[0][1]
ax.plot(steps, comp_tokens, "g-o", markersize=4)
ax.set_xlabel("Training Step")
ax.set_ylabel("Tokens")
ax.set_title("📝 Completion Tokens — Response length over training")
ax.grid(True, alpha=0.3)

# 3. Reasoning tokens (how hard the model is thinking)
reason_tokens = [float(r.get("reasoning_tokens_mean", 0) or 0) for r in metrics]
ax = axes[1][0]
ax.plot(steps, reason_tokens, "m-o", markersize=4)
ax.set_xlabel("Training Step")
ax.set_ylabel("Tokens")
ax.set_title("🧠 Reasoning Tokens — How hard is the model thinking?")
ax.grid(True, alpha=0.3)

# 4. Tool call errors (is the model making valid tool calls?)
tool_errors = [float(r.get("train_error_count_get_order", 0) or 0) * 100 for r in metrics]
ax = axes[1][1]
ax.plot(steps, tool_errors, "r-o", markersize=4)
ax.set_xlabel("Training Step")
ax.set_ylabel("Error Rate (%)")
ax.set_title("🔧 Tool Call Errors — Drops as model learns")
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("results/training_dashboard.png", dpi=150)
plt.show()
```
**What this code does:**
Imports required Python libraries and prepares the runtime environment.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
A chart or map rendered inline in the notebook.

### Code Cell 19

1. Run the below cell.

```python
# Key takeaways from the training metrics
print("📊 What the metrics tell us:\n")
print(f"  Reward:    {train_rewards[0]:.3f} → {train_rewards[-1]:.3f}  (model learned to score higher)")
print(f"  Comp tokens: {comp_tokens[0]:.0f} → {comp_tokens[-1]:.0f}    (responses got more detailed)")
print(f"  Reasoning: {reason_tokens[0]:.0f} → {reason_tokens[-1]:.0f}    (model is 'thinking harder')")
print(f"  Tool errors: {tool_errors[0]:.1f}% → {tool_errors[-1]:.1f}%  (learned to make valid tool calls)")
print()
print("💡 Watch for these during training:")
print("   ✅ Reward increasing = model is learning")
print("   ✅ Tool errors decreasing = model making better tool calls")
print("   ⚠️  Completion tokens growing fast = possible verbosity bloat")
print("   ⚠️  Reasoning tokens doubling = more inference cost per request")
```
**What this code does:**
Retrieves job status or evaluates model/checkpoint performance.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 20

1. Run the below cell.

```python
# Pre-computed checkpoint results
checkpoints = {
    "Base o4-mini": {"avg": 0.732, "p90": 0.37, "p80": 0.60},
    "Step 70 (peak valid reward)": {"avg": 0.855, "p90": 0.47, "p80": 0.83},
    "Step 95 (best eval)": {"avg": 0.867, "p90": 0.50, "p80": 0.90},
}

print(f"{'Model':<35} {'Avg Score':>10} {'P@0.9':>8} {'P@0.8':>8}")
print(f"{'-'*35} {'-'*10} {'-'*8} {'-'*8}")
for name, r in checkpoints.items():
    print(f"{name:<35} {r['avg']:>9.1%} {r['p90']:>7.0%} {r['p80']:>7.0%}")
```
**What this code does:**
Retrieves job status or evaluates model/checkpoint performance.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 21

1. Run the below cell.

```python
# Evaluate fine-tuned model on the same scenarios
# (Uses the deployment name of the pre-deployed RFT model)
RFT_MODEL = "rft-v7-py80-step95"  # <-- pre-deployed by facilitator

print(f"Evaluating {RFT_MODEL} on {len(eval_scenarios)} scenarios...\n")
rft_scores = []

for i, ex in enumerate(eval_scenarios):
    msg = ex["messages"][-1]["content"]
    expected = ex.get("expected_resolution", "")

    output, tools = run_agent(msg, model=RFT_MODEL, verbose=False)
    score = python_grader(output, tools, expected)
    rft_scores.append(score)

    # Show comparison with base
    base_sc = base_scores[i]
    delta = score - base_sc
    arrow = "📈" if delta > 0.05 else ("📉" if delta < -0.05 else "➡️")
    print(f"  [{i+1:2d}] base={base_sc:.3f} → rft={score:.3f} ({delta:+.3f}) {arrow}  {msg[:45]}")

rft_avg = sum(rft_scores) / len(rft_scores)
rft_p90 = sum(1 for s in rft_scores if s >= 0.9) / len(rft_scores)
rft_p80 = sum(1 for s in rft_scores if s >= 0.8) / len(rft_scores)
```
**What this code does:**
Retrieves job status or evaluates model/checkpoint performance.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 22

1. Run the below cell.

```python
# Head-to-head summary
print(f"\n{'='*60}")
print(f"  HEAD-TO-HEAD COMPARISON")
print(f"{'='*60}")
print(f"  {'Metric':<20} {'Base o4-mini':>15} {'RFT Model':>15} {'Delta':>10}")
print(f"  {'-'*20} {'-'*15} {'-'*15} {'-'*10}")
print(f"  {'Average score':<20} {base_avg:>14.1%} {rft_avg:>14.1%} {rft_avg-base_avg:>+9.1%}")
print(f"  {'Pass@0.9 (strict)':<20} {base_p90:>14.0%} {rft_p90:>14.0%} {rft_p90-base_p90:>+9.0%}")
print(f"  {'Pass@0.8 (good)':<20} {base_p80:>14.0%} {rft_p80:>14.0%} {rft_p80-base_p80:>+9.0%}")
print(f"{'='*60}")

# Visualize
improved = sum(1 for b, r in zip(base_scores, rft_scores) if r > b + 0.05)
same = sum(1 for b, r in zip(base_scores, rft_scores) if abs(r - b) <= 0.05)
worse = sum(1 for b, r in zip(base_scores, rft_scores) if r < b - 0.05)
print(f"\n  Improved: {improved}/{len(base_scores)} scenarios")
print(f"  Same:     {same}/{len(base_scores)} scenarios")
print(f"  Worse:    {worse}/{len(base_scores)} scenarios")
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

