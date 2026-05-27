# Demo: Zava-Next — Multi-Tool Post-Purchase Resolution Agent

## What is Zava-Next?

**Zava-Next** is a 6-tool AI agent that handles post-purchase customer resolutions for a fictional e-commerce company called *Zava*. It processes returns, exchanges, replacements, cancellations, and shipping disputes by calling tools in a structured workflow.

Unlike simple chatbots that handle one-shot Q&A, Zava-Next must:
- **Orchestrate multiple tool calls** in the correct sequence
- **Apply complex business rules** (return windows by tier, restocking fees, sale item policies)
- **Handle multi-item orders** where each item may have a different resolution

This makes it an ideal candidate for evaluating how different base models handle multi-step agentic reasoning — and how Reinforcement Fine-Tuning (RFT) can improve that behavior.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Azure AI Foundry                      │
│  ┌──────────────────────────────────────────────┐    │
│  │         Hosted Agent Container                │    │
│  │                                               │    │
│  │  ┌─────────┐    ┌──────────────────────┐    │    │
│  │  │ Agent   │───▶│  Base Model (LLM)    │    │    │
│  │  │ Server  │◀───│  (o4-mini, gpt-4.1,  │    │    │
│  │  │         │    │   gpt-5.4-mini, etc.) │    │    │
│  │  └────┬────┘    └──────────────────────┘    │    │
│  │       │                                       │    │
│  └───────┼───────────────────────────────────────┘    │
│          │                                            │
│          │  Traces (auto-collected)                    │
│          ▼                                            │
│    App Insights                                       │
└──────────────────────────────────────────────────────┘
           │
           │ HTTP (tool calls)
           ▼
┌──────────────────────────────┐
│  Tool Server (Azure Function) │
│  zava-next-tools-*.net        │
│                               │
│  • get_order_details          │
│  • get_fulfillment_status     │
│  • check_resolution_policy    │
│  • check_inventory            │
│  • calculate_resolution       │
│  • submit_resolution          │
└──────────────────────────────┘
```

### The 6 Tools

| # | Tool | Purpose | When to Call |
|---|------|---------|-------------|
| 1 | `get_order_details` | Retrieve order info, line items, customer loyalty tier | Always first |
| 2 | `get_fulfillment_status` | Check delivery status, late delivery, lost packages | Always second |
| 3 | `check_resolution_policy` | Verify return/exchange eligibility per item | Once per item |
| 4 | `check_inventory` | Check stock for exchange SKU | Only for exchanges |
| 5 | `calculate_resolution` | Compute refund amounts, fees, credits | After policy checks |
| 6 | `submit_resolution` | Finalize the resolution | Only after calculate |

### Business Rules (embedded in system prompt)

- **Return windows** vary by loyalty tier (Standard/Gold/Platinum) and category (Apparel, Electronics, Personal Care)
- **Restocking fees** apply to non-defective electronics (15%/7.5%/0% by tier)
- **Sale items** are final sale (no returns) unless defective → store credit only
- **Late delivery** (>2 days): $10 shipping credit + extended return window
- **Lost packages**: full replacement or refund, no restocking fee
- **Defective items**: always eligible regardless of window/sale/category

---

## Deploying Zava-Next

### Prerequisites

Complete the [project setup](./SETUP_PREREQ.md) first (creates Azure AI Foundry project with working traces).

### Deploy a Single Agent (Validate First)

Start with one model to verify everything works:

```bash
cd demo-v2
./scripts/deploy_agent.sh zava-next o4-mini
```

The script will:
1. Generate a concrete manifest from the template
2. Deploy the `o4-mini` model if not already present
3. Deploy the agent container
4. Grant the required IAM role

> ⚠️ `azd ai agent init` is interactive — accept the defaults when prompted.

### Test the Agent

```bash
cd demo-v2/deploy
azd ai agent invoke --message "I need to return the headphones from order ORD-005, they are defective"
```

**Expected behavior:** The agent should call tools in sequence:
1. `get_order_details("ORD-005")` → retrieves order info
2. `get_fulfillment_status("ORD-005")` → checks delivery status
3. `check_resolution_policy("ORD-005", "LI-xxx", "defective")` → confirms eligibility
4. `calculate_resolution(...)` → computes refund (0% restocking fee for defective)
5. `submit_resolution(...)` → confirms the return

### Verify Traces

In the Azure AI Foundry portal:
1. Open your project → **Tracing** tab
2. You should see the full tool-call chain with latencies
3. Each tool invocation appears as a separate span

---

## Deploying Multiple Base Models

The goal is to compare how different models handle the same agentic workflow. Deploy one agent per model:

```bash
cd demo-v2

# Already deployed:
# ./scripts/deploy_agent.sh zava-next o4-mini

# Deploy remaining models:
./scripts/deploy_agent.sh zava-next gpt-4.1
./scripts/deploy_agent.sh zava-next gpt-4.1-mini
./scripts/deploy_agent.sh zava-next gpt-4.1-nano
./scripts/deploy_agent.sh zava-next gpt-5.4
./scripts/deploy_agent.sh zava-next gpt-5.4-mini
```

### Model Deployment Reference

| Agent Name | Model | SKU | Capacity | Status |
|-----------|-------|-----|----------|--------|
| `zava-next-o4-mini` | o4-mini | GlobalStandard | 1000 TPM | ✅ Active |
| `zava-next-gpt-4-1` | gpt-4.1 | GlobalStandard | 8637 TPM | ✅ Active |
| `zava-next-gpt-4-1-mini` | gpt-4.1-mini | Standard | 50 TPM | ✅ Active |
| `zava-next-gpt-4-1-nano` | gpt-4.1-nano | GlobalStandard | 50 TPM | ✅ Active |
| `zava-next-gpt-5-4` | gpt-5.4 | GlobalStandard | 50 TPM | ✅ Active |
| `zava-next-gpt-5-4-mini` | gpt-5.4-mini | GlobalStandard | 50 TPM | ✅ Active |

**Project:** `ai-project-omi-build26-azd-env`  
**Account:** `ai-account-44mf5lkxqssxm`  
**Region:** North Central US  
**Resource Group:** `rg-omi-build26-azd-env`

### Agent Endpoints

All agents share the same base URL pattern:
```
https://ai-account-44mf5lkxqssxm.services.ai.azure.com/api/projects/ai-project-omi-build26-azd-env/agents/<agent-name>/endpoint/protocols/openai/responses?api-version=2025-11-15-preview
```

### What We're Comparing

With multiple base models deployed, we can evaluate:

1. **Tool-call accuracy** — Does the model call the right tools in the right order?
2. **Policy adherence** — Does it correctly apply restocking fees, return windows, sale rules?
3. **Multi-item handling** — Can it process orders with multiple items needing different resolutions?
4. **Efficiency** — How many turns/tokens does it take to complete a resolution?
5. **Error patterns** — Where does each model fail? (e.g., skipping `calculate_resolution`, wrong fee %)

---

## Evaluation (Coming Next)

> 📋 This section will be populated after running evaluations.

### The Zava Database — Test Scenarios

The agent operates over a synthetic e-commerce database (`data/zava_db.json`) designed to cover all policy edge cases:

| Dimension | Coverage |
|-----------|----------|
| **Customers** | 5 customers across 3 loyalty tiers (Platinum, Gold, Standard) |
| **Products** | 28 SKUs across 4 categories (Electronics, Apparel, Home, Personal Care) |
| **Orders** | 12 orders with 1–2 line items each, various fulfillment states |
| **Inventory** | 13 SKUs tracked (some out-of-stock for exchange testing) |
| **Today's date** | 2026-07-15 (controls return window calculations) |

#### Scenario Design Principles

The database is constructed so that each order tests specific policy dimensions:

- **Return window edge cases** — orders with deliveries at exactly 15/30/45/60 days ago
- **Tier-specific rules** — same product/reason combinations across Standard/Gold/Platinum customers
- **Sale items** — some items marked `on_sale: true` (final sale unless defective)
- **Late deliveries** — orders with `late_delivery: true` (triggers $10 credit + window extension)
- **Lost packages** — fulfillment status `lost` (full replacement/refund, no restocking)
- **Multi-item orders** — orders requiring per-item resolution with different outcomes

#### 📊 Interactive Data Explorer

Open the dashboard to explore all scenarios, customers, orders, and products interactively:

**[→ Open Data Dashboard](data/dashboard.html)**

The dashboard includes:
- **Overview** — Stats and distribution charts
- **Customers** — Profile cards with tier info and order history
- **Orders** — Full order details with fulfillment status per item
- **Products** — Catalog with inventory status and sale indicators
- **Eval Scenarios** — All 254 scenarios (filterable by resolution type, dataset split)
- **Distribution** — Train/val split analysis, category coverage, tier × resolution breakdown

### Eval Dataset

| Split | Count | Purpose |
|-------|-------|---------|
| **Train** | 192 scenarios | Used for RFT training signal |
| **Validation** | 62 scenarios | Held out for eval — never seen during training |

**Resolution type distribution (Train):**

| Type | Count | % |
|------|-------|---|
| Refund | 84 | 44% |
| Deny | 60 | 31% |
| Exchange | 36 | 19% |
| Cancellation | 8 | 4% |
| Replacement | 4 | 2% |

Each scenario includes:
- A `developer` message (system prompt)
- A `user` message (customer request)
- An `expected_resolution` (ground truth for evaluation)

### Running Evaluations

*Instructions to be added after validating the eval pipeline.*

### Results

*Comparison table across models to be added after eval runs complete.*

---

## Traces & Observability

Every agent invocation produces traces in Azure Application Insights, visible in the Foundry portal. Key metrics to watch:

| Metric | What It Shows |
|--------|--------------|
| Total tool calls per request | Efficiency of the model's planning |
| Tool call sequence | Whether the model follows the required workflow |
| Latency per tool call | Where time is spent |
| Error rate | Failed tool calls or policy violations |
| Token usage | Cost comparison across models |

### Example Trace (Expected)

```
├── Agent Invocation
│   ├── LLM Call → decides to call get_order_details
│   ├── Tool: get_order_details (200ms)
│   ├── LLM Call → decides to call get_fulfillment_status
│   ├── Tool: get_fulfillment_status (180ms)
│   ├── LLM Call → decides to call check_resolution_policy
│   ├── Tool: check_resolution_policy (150ms)
│   ├── LLM Call → decides to call calculate_resolution
│   ├── Tool: calculate_resolution (160ms)
│   ├── LLM Call → decides to call submit_resolution
│   ├── Tool: submit_resolution (140ms)
│   └── LLM Call → generates final response
└── Total: ~2.5s (6 tool calls + 6 LLM calls)
```

---

## Running Evaluations

### Prerequisites

1. **Agents deployed** (see deployment section above)
2. **Validation dataset uploaded** to Azure AI Foundry
   - Dataset name: `omi-dataset-val:1`
   - Upload via: AI Foundry Portal → Data → Upload JSONL
   - Source file: `data/rft_next_val.jsonl` (62 scenarios)

### Option 1: Foundry UI (Recommended for Demo)

**Why:** Results are visible in Foundry portal with built-in visualizations

1. Open **`03_run_evaluations.ipynb`**
2. Run all cells sequentially
3. The notebook will:
   - Create evaluation definition with custom Python grader
   - Launch eval runs for all 6 models
   - Monitor progress (auto-polls every 30s)
   - Display comparative results table

**View Results:**
- In notebook: See pass rates and per-criteria scores
- Foundry Portal: `https://ai.azure.com` → Evaluations → `zava-multi-model-eval`
- Traces tab: See per-scenario agent behavior

### Option 2: Local Python (Fastest)

**Why:** Immediate results, no waiting for Foundry runs

```bash
cd demo-v2/eval
python3 run_local_eval.py --model o4-mini --scenarios 62
```

Results saved to `eval/local_eval_results.json`

### Evaluation Metrics

Our custom grader scores on 3 dimensions:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Decision Correctness** | 50% | Did the agent choose the right action (refund/deny/exchange)? |
| **Financial Accuracy** | 30% | Are dollar amounts correct (±$2 tolerance)? |
| **Format Compliance** | 20% | Does output follow the required format? |

**Pass threshold:** 80% (scenarios scoring ≥0.8 pass)

### Interpreting Results

**Good performance indicators:**
- Decision correctness >85%
- Financial accuracy >90% (simple arithmetic)
- Format compliance >75% (structured output)

**Common failure modes:**
- Exchange scenarios: Models often deny instead of exchanging
- Multi-item orders: Format compliance drops
- Edge cases: Defective sale items (store credit only)

### Next: RFT Training

After baseline evaluation, use the best-performing model for RFT training:

```bash
# See notebook: 04_rft_training.ipynb
```

---

## File Reference

| Path | Purpose |
|------|---------|
| `agents/zava-next/main.py` | Agent source code (shared across all model variants) |
| `agents/zava-next/agent.manifest.yaml` | Template manifest with `{{MODEL_ID}}` placeholder |
| `agents/zava-next/Dockerfile` | Container build spec |
| `scripts/deploy_agent.sh` | Deploy single agent (model + agent + role) |
| `scripts/deploy_all.sh` | Batch deploy all models |
| `tools/zava-next-tools/function_app.py` | Tool server (Azure Function) |
| `data/rft_next_val.jsonl` | Validation dataset (62 scenarios) |
| `data/rft_next_train.jsonl` | Training dataset (343 scenarios) |
| `eval/zava_grader_response.py` | Response-only grader (for hosted agents) |
| `eval/zava_grader_agentic.py` | Full grader with tool-call validation (for RFT reward) |
| `eval/check_foundry_status.py` | CLI tool to monitor eval runs |
| `03_run_evaluations.ipynb` | **Notebook: Run multi-model evaluations** |
