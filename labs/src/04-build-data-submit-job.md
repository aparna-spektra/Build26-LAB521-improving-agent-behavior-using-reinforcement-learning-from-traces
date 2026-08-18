# Lab: Build Data Submit Job

## 📘 Lab Scenario
In this lab, you will work through the notebook src\04-build-data-submit-job.ipynb and execute each code cell in sequence to complete the workflow successfully.

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
# Workaround: use direct Azure OpenAI endpoint client to avoid project-identity RBAC path.
from openai import OpenAI
client = OpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"]
)
print("✅ Switched to direct Azure OpenAI client")
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

### Code Cell 5

1. Run the below cell.

```python
# Dataset overview
with open("data/rft_v7_train.jsonl") as f:
    train_data = [json.loads(line) for line in f]
with open("data/rft_v7_val.jsonl") as f:
    val_data = [json.loads(line) for line in f]

print(f"Training examples: {len(train_data)}")
print(f"Validation examples: {len(val_data)}")
print(f"\nSample user messages from training set:")
for i, ex in enumerate(train_data[:5]):
    user_msg = ex["messages"][-1]["content"]
    print(f"  [{i+1}] {user_msg[:80]}..." if len(user_msg) > 80 else f"  [{i+1}] {user_msg}")
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

### Code Cell 6

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

### Code Cell 7

1. Run the below cell.

```python


my_example = {
    "messages": [
        {"role": "developer", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Yusuf Rossi here. The keyboard from ORD-003 stopped working after a week. Keys are unresponsive."}
    ],
    "expected_resolution": "Refund $89.99 for defective keyboard. Gold tier, within 45-day window. Defective items have $0 restocking fee."
}

# Test: what does base gpt-5-mini say for our example?
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

### Code Cell 8

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

### Code Cell 9

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

### Code Cell 10

1. Run the below cell.

```python
# Step 4: Submit the job!
TOOL_CONFIG = [
    {"name": "get_order",
     "server_url": f"{TOOL_URL}/tool/get_order",
     "headers": {}}
]

job = client.fine_tuning.jobs.create(
    model="gpt-5",
    training_file=train_file.id,
    validation_file=val_file.id,
    suffix="zava-lab",
    method={"type": "reinforcement", "reinforcement": {
        "grader": {
            "type": "python",
            "name": "zava_grader",
            "source": GRADER_SOURCE.strip(),
            "pass_threshold": 0.80,
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
    extra_body={
        "trainingType": "globalStandard"
    }
)

print(f"🚀 Job submitted!")
print(f"   ID: {job.id}")
print(f"   Status: {job.status}")
print(f"   Model: {job.model}")
print(f"\n⏳ Training can take 10 hours. We'll explore pre-run results next.")
```
**What this code does:**
Submits a fine-tuning job with the configured model, grader, and hyperparameters.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
A job ID and initial job status such as pending or queued. If validation fails, an API error message is returned.

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

