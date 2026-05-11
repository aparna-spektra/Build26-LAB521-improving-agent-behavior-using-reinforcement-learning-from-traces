# %% [markdown]
# # 🏪 Zava Agentic Fine-Tuning Lab
#
# **Learn how reinforcement fine-tuning (RFT) improves AI agents that use tools.**
#
# You'll work with Zava, a fictional retailer whose AI agent resolves returns, exchanges, and disputes
# by calling tools and applying complex business policy. By the end of this lab, you'll see how RFT
# teaches the model to make better decisions — improving accuracy from ~73% to ~87%.
#
# | Section | What You'll Do | Time |
# |---------|---------------|------|
# | 1. Setup | Connect to Microsoft Foundry | 5 min |
# | 2. Meet the Agent | Run the agent live, see tool calling in action | 10 min |
# | 3. Baseline | Evaluate base o4-mini on 30 scenarios | 10 min |
# | 4. The Grader | Understand how RFT scores the model's responses | 5 min |
# | 5. Build Data | Create training examples, understand the format | 5 min |
# | 6. Submit a Job | Configure and submit your own RFT training job | 10 min |
# | 7. Training Results | Explore reward curves, tool calls, and token usage | 10 min |
# | 8. Evaluate | Compare the fine-tuned model head-to-head with base | 10 min |
# | 9. Wrap-Up | Key takeaways and next steps | 5 min |
#
# > **Prerequisites**: Python 3.10+, an Microsoft Foundry project with o4-mini deployed.
# > Your facilitator has pre-deployed the tool endpoints and fine-tuned models.

# %% [markdown]
# ---
# ## 1. Setup (5 min)
#
# Connect to your Microsoft Foundry project. Your `.env` file should contain:
# ```
# AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com/api/projects/<your-project>/openai/v1/
# AZURE_OPENAI_API_KEY=<your-key>
# ```

# %%
# Install dependencies (uncomment if needed)
# %pip install -q openai python-dotenv requests tabulate matplotlib

# %%
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
    max_completion_tokens=10,
)
print(f"✅ Connected! Model responded: {test.choices[0].message.content}")

# %% [markdown]
# ---
# ## 2. Meet the Agent (10 min)
#
# Zava's return resolution agent uses a **tool** (`get_order`) to look up order details,
# then applies a complex return policy to determine the correct resolution.
#
# ### The Policy (deliberately complex — this is what makes it hard for the model)
#
# | Rule | Details |
# |------|---------|
# | Return windows | Standard: 30d, Gold: 45d, Platinum: 60d (electronics: 15d/30d/45d) |
# | Electronics restocking | Standard: 15%, Gold: 7.5%, Platinum: 0% |
# | Defective items | Always free return, $0 restocking |
# | Sale items | Final sale (defective sale → store credit only) |
# | Late delivery (>2 days) | $10 shipping credit + 15-day window extension |
# | Lost/pending orders | Replacement/refund or cancellation |
# | Opened personal care | Deny unless defective |

# %%
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


def run_agent(user_message, model="o4-mini", verbose=True):
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

# %% [markdown]
# ### Try it! Run the agent on a few scenarios.

# %%
# Scenario 1: Defective electronics return (should be easy)
print("=" * 60)
print("SCENARIO 1: Defective headphones")
print("=" * 60)
response, tools = run_agent(
    "Hi, I'm Ava Chen. The headphones from ORD-002 have a cracked speaker. I want a refund."
)

# %%
# Scenario 2: Complex — sale item + defective (tricky policy interaction)
print("=" * 60)
print("SCENARIO 2: Defective sale item")
print("=" * 60)
response, tools = run_agent(
    "Emma Kim. The face serum from ORD-004 caused a skin reaction. It was on sale but it's defective."
)

# %%
# Scenario 3: Exchange request (the model often struggles with these)
print("=" * 60)
print("SCENARIO 3: Exchange request")
print("=" * 60)
response, tools = run_agent(
    "Noah Brown. Exchange hiking boots from ORD-010 for size 11."
)

# %% [markdown]
# > **💡 Notice**: The agent calls `get_order` to look up the real order data, then reasons about
# > the policy to determine the resolution. Sometimes it gets the action right but the amount wrong,
# > or misses a policy nuance. That's what we'll improve with fine-tuning.

# %% [markdown]
# ---
# ## 3. Baseline Evaluation (10 min)
#
# Before fine-tuning, we need to know how well the base model performs.
# We'll score it on 30 validation scenarios using a **grader** that checks:
# - Did it get the right **action** (refund, deny, store credit)? (40%)
# - Did it compute the correct **dollar amounts**? (30%)
# - Did it cite the right **policy reasons**? (20%)
# - Did it **use the tool**? (10%)

# %%
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

# %%
# Load validation scenarios
with open("data/rft_v7_val.jsonl") as f:
    val_scenarios = [json.loads(line) for line in f]

print(f"Loaded {len(val_scenarios)} validation scenarios")
print(f"Sample: {val_scenarios[0]['messages'][-1]['content'][:80]}...")

# %%
# Run baseline evaluation (takes ~5-8 minutes with 30 scenarios)
import random
random.seed(42)
eval_scenarios = random.sample(val_scenarios, min(30, len(val_scenarios)))

print(f"Evaluating base o4-mini on {len(eval_scenarios)} scenarios...\n")
base_scores = []

for i, ex in enumerate(eval_scenarios):
    msg = ex["messages"][-1]["content"]
    expected = ex.get("expected_resolution", "")

    output, tools = run_agent(msg, model="o4-mini", verbose=False)
    score = python_grader(output, tools, expected)
    base_scores.append(score)

    status = "✅" if score >= 0.9 else ("⚠️" if score >= 0.5 else "❌")
    print(f"  [{i+1:2d}] {score:.3f} {status}  {msg[:55]}")

base_avg = sum(base_scores) / len(base_scores)
base_p90 = sum(1 for s in base_scores if s >= 0.9) / len(base_scores)
base_p80 = sum(1 for s in base_scores if s >= 0.8) / len(base_scores)

print(f"\n{'='*50}")
print(f"  BASE o4-mini RESULTS")
print(f"  Average score: {base_avg:.1%}")
print(f"  Pass@0.9 (strict): {base_p90:.0%}")
print(f"  Pass@0.8 (good): {base_p80:.0%}")
print(f"{'='*50}")

# %% [markdown]
# ---
# ## 4. The Grader — How RFT Learns (5 min)
#
# RFT works differently from SFT (supervised fine-tuning):
#
# | | SFT | RFT |
# |---|-----|-----|
# | Data | Prompt + ideal response pairs | Prompts only (+ grader) |
# | Signal | "Copy this response" | "This attempt scored 0.85 — try to do better" |
# | Best for | Teaching format/style | Improving reasoning/accuracy |
#
# The **grader** is the key to RFT. It scores each training rollout, and the model learns to
# maximize its score. Our grader gives **partial credit** — crucial for learning:
#
# ```
# score = 0.4 × action_correct + 0.3 × amount_correct + 0.2 × policy_reasoning + 0.1 × tool_usage
# ```
#
# The **pass_threshold** determines what score counts as success vs failure for the RL reward.
# Let's see how different thresholds affect the training signal:

# %%
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

# %% [markdown]
# ---
# ## 5. Build Training Data (5 min)
#
# RFT training data is simpler than SFT — you only need **prompts** (not ideal responses).
# The model generates its own responses during training, and the grader scores them.
#
# Each example needs:
# - `messages` — the conversation (developer prompt + user request)
# - `expected_resolution` — the correct answer, used by the grader to score
#
# **You don't write model responses!** The model figures those out through trial and error.

# %%
# Let's look at the data format
sample = json.loads(open("data/rft_v7_train.jsonl").readline())
print("Training example format:")
print(json.dumps(sample, indent=2)[:600])

# %% [markdown]
# ### Build your own example
#
# Let's create a training example from scratch. First, call the tool to see what
# order data is available, then write the expected resolution.

# %%
# Look up an order to understand the data
order_data = call_tool("get_order", {"order_id": "ORD-003"})
print("Order ORD-003 data:")
print(json.dumps(json.loads(order_data), indent=2))

# %%
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

# %% [markdown]
# > **💡 Key insight**: For RFT, data diversity matters more than volume.
# > We wrote ~40 unique scenarios by hand, then used an LLM to generate 10 rephrasings
# > of each (different tones, wordings, levels of detail). That gives 400 examples that
# > teach the model to handle the same policy rules with varied customer phrasings.
# >
# > Our pre-built dataset (`rft_v7_train.jsonl`) has 343 examples built this way.

# %% [markdown]
# ---
# ## 6. Submit an RFT Job (10 min)
#
# Now let's submit a real RFT training job with the pre-built dataset.

# %%
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

# %%
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

# %%
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

# %% [markdown]
# ---
# ## 7. Explore Training Results (10 min)
#
# While your job queues, let's look at results from a completed run.
# We pre-ran the same experiment — here's what happened during training.

# %%
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

# %%
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

# %% [markdown]
# ### Checkpoint comparison
#
# RFT saves checkpoints periodically. The best checkpoint isn't always the last one!
# Always evaluate multiple checkpoints with your actual task metric.

# %%
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

# %% [markdown]
# ---
# ## 8. Evaluate the Fine-Tuned Model (10 min)
#
# The pre-deployed fine-tuned model is available as `rft-v7-py80-step95`.
# Let's run it on the same scenarios and compare head-to-head.

# %%
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

# %%
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

# %% [markdown]
# ---
# ## 9. Wrap-Up & Key Takeaways (5 min)
#
# ### What we learned
#
# 1. **RFT improves agentic tool-calling tasks** — the model learned to apply policy rules
#    more accurately without being shown the "right" answer.
#
# 2. **The grader is everything** — partial credit (not binary pass/fail) is critical.
#    The model needs gradient signal to learn incrementally.
#
# 3. **Calibrate your pass threshold** — target 30-50% failure rate on the base model.
#    Too easy = no signal. Too hard = sparse reward.
#
# 4. **Always evaluate checkpoints** — the best checkpoint isn't always the last one.
#    Training metrics don't perfectly predict real-world performance.
#
# 5. **Start small, iterate fast** — we validated with 60 examples first, then scaled
#    to 343. Don't invest in a large dataset until the grader and threshold are working.
#
# ### What to try next
#
# - **Your submitted job** will finish in 2-4 hours — check the reward curve!
# - Try a **tighter threshold** (0.85 or 0.90) for stricter policy compliance
# - Try **more training data** — generate additional scenario variations
# - Try **different hyperparameters** — lower learning rate for smoother convergence
# - Compare with **SFT distillation** — use a large model's outputs as training data
#
# ### Resources
# - [Azure AI Fine-Tuning docs](https://learn.microsoft.com/azure/ai-services/openai/how-to/fine-tuning)
# - [RFT with graders guide](https://developers.openai.com/api/docs/guides/graders)
# - [Agentic RFT with tools](https://developers.openai.com/api/docs/guides/reinforcement-fine-tuning)