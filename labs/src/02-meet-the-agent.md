# Lab: Meet The Agent

## 📘 Lab Scenario
In this lab, you will work through the notebook src\02-meet-the-agent.ipynb and execute each code cell in sequence to complete the workflow successfully.

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
# Scenario 1: Defective headphones
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

### Code Cell 4

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

### Code Cell 5

1. Run the below cell.

```python
# Scenario 3: Exchange request
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

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

