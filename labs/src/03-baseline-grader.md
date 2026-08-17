# Lab: Baseline Grader

## 📘 Lab Scenario
In this lab, you will work through the notebook src\03-baseline-grader.ipynb and execute each code cell in sequence to complete the workflow successfully.

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
import json, os, re, time, textwrap
import requests
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv(override=True)

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential = DefaultAzureCredential()
)
client = project_client.get_openai_client(api_key=os.environ["AZURE_OPENAI_API_KEY"])
print("✅ Connected to Microsoft Foundry")
```
**What this code does:**
Authenticates and configures service clients used throughout the lab.

**Before you run this cell:**
Ensure required environment variables, credentials, and files are available before running this first cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 2

1. Run the below cell.

```python
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
    """Call the Zava tool endpoint and return the result."""
    url = f"{TOOL_URL}/tool/{name}"
    payload = {"arguments": json.dumps(args), "call_id": "c", "id": "f", "trace_id": "t"}
    r = requests.post(url, json=payload, timeout=30)
    return r.json().get("output", json.dumps(r.json()))


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
Defines reusable helper logic that later cells execute.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 3

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

### Code Cell 4

1. Run the below cell.

```python
# Load validation scenarios
with open("data/rft_v7_val.jsonl") as f:
    val_scenarios = [json.loads(line) for line in f]

print(f"Loaded {len(val_scenarios)} validation scenarios")
print(f"Sample: {val_scenarios[0]['messages'][-1]['content'][:80]}...")
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 5

1. Run the below cell.

```python
import os

GT_FILE = "data/rft_v7_val_gt.jsonl"

if os.path.exists(GT_FILE):
    with open(GT_FILE) as f:
        val_scenarios = [json.loads(line) for line in f]
    print(f"✅ Loaded {len(val_scenarios)} scenarios with cached ground truth")
    sample = val_scenarios[0].get("expected_resolution", "")[:120]
    print(f"   Sample resolution: {sample}...")
else:
    print(f"Generating ground truth for {len(val_scenarios)} scenarios using gpt-5.4...")
    print("(~15–20 min — results cached to avoid re-running)\n")

    gt_scenarios = []
    for i, ex in enumerate(val_scenarios):
        msg = ex["messages"][-1]["content"]
        output, _ = run_agent(msg, model="gpt-5.4", verbose=False)
        ex_with_gt = dict(ex)
        ex_with_gt["expected_resolution"] = output
        gt_scenarios.append(ex_with_gt)
        print(f"  [{i+1:2d}/{len(val_scenarios)}] {msg[:70]}...")

    with open(GT_FILE, "w") as f:
        for ex in gt_scenarios:
            f.write(json.dumps(ex) + "\n")

    val_scenarios = gt_scenarios
    print(f"\n✅ Ground truth saved to {GT_FILE}")
    print(f"   Re-run this cell anytime to reload from cache")
```
**What this code does:**
Imports required Python libraries and prepares the runtime environment.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

### Code Cell 6

1. Run the below cell.

```python
# Run baseline evaluation (takes ~5-8 minutes with 30 scenarios)
import random
random.seed(42)
eval_scenarios = random.sample(val_scenarios, min(8, len(val_scenarios)))

print(f"Evaluating base gpt-5-mini on {len(eval_scenarios)} scenarios...\n")
base_scores = []

for i, ex in enumerate(eval_scenarios):
    msg = ex["messages"][-1]["content"]
    expected = ex.get("expected_resolution", "")

    output, tools = run_agent(msg, model="gpt-5-mini", verbose=False)
    score = python_grader(output, tools, expected)
    base_scores.append(score)

    status = "✅" if score >= 0.9 else ("⚠️" if score >= 0.5 else "❌")
    print(f"  [{i+1:2d}] {score:.3f} {status}  {msg[:55]}")

base_avg = sum(base_scores) / len(base_scores)
base_p90 = sum(1 for s in base_scores if s >= 0.9) / len(base_scores)
base_p80 = sum(1 for s in base_scores if s >= 0.8) / len(base_scores)

print(f"\n{'='*50}")
print(f"  BASE gpt-5-mini RESULTS")
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

### Code Cell 7

1. Run the below cell.

```python
# Calibration: what threshold gives the right failure rate?
print("Pass threshold calibration (base gpt-5-mini):\n")
print(f"  {'Threshold':>10} {'Pass Rate':>10} {'Fail Rate':>10} {'Signal Quality':>15}")
print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*15}")

for threshold in [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95]:
    pass_rate = sum(1 for s in base_scores if s >= threshold) / len(base_scores)
    fail_rate = 1 - pass_rate
    quality = "✅ Good (25-50%)" if 0.25 <= fail_rate <= 0.50 else ("⚠️ Too easy" if fail_rate < 0.25 else "⚠️ Too hard")
    print(f"  {threshold:>10.2f} {pass_rate:>9.0%} {fail_rate:>9.0%} {quality:>15}")

print(f"\n💡 From our experiments pass_threshold=0.80 gives on average 35% failure rate → good learning signal")
```
**What this code does:**
Prints progress, identifiers, or computed outputs for validation.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

