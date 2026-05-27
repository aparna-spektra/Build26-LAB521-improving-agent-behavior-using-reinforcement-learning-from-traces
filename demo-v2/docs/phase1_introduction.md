# Phase 1: Introduction to Zava-Next Agent

**Demo Time:** 10-12 minutes  
**Status:** Complete ✅

---

## 🎯 Objectives

By the end of Phase 1, the audience should understand:
1. What Zava-Next agent does (post-purchase resolution)
2. The 6-tool workflow and business rules
3. The evaluation world (database, scenarios)
4. How to deploy agents on Azure AI Foundry
5. How traces work for observability

---

## 📋 Prerequisites

- Azure AI Foundry project created (see `SETUP_PREREQ.md`)
- Traces enabled and validated
- Tool server deployed (`zava-next-tools`)
- At least one agent deployed for demo

---

## 🎬 Demo Script

### 1. Introduce the Problem (2 min)

**Story:** "Zava is an e-commerce company that handles returns, exchanges, and replacements. Their customer service team needs an AI agent that can automatically process these requests while following complex business rules."

**Key Points:**
- Multi-step workflow (not simple Q&A)
- Business rules vary by customer tier, product category, delivery status
- Agent must orchestrate multiple tools in correct order
- This is hard for base models — ideal for RL improvement

---

### 2. Show the Zava-Next Architecture (2 min)

**Visual:** Show architecture diagram from `demo-zava-next.md`

**The 6 Tools:**
1. `get_order_details` — Retrieve order info
2. `get_fulfillment_status` — Check delivery status
3. `check_resolution_policy` — Verify eligibility
4. `check_inventory` — Check stock for exchanges
5. `calculate_resolution` — Compute refunds/fees
6. `submit_resolution` — Finalize action

**Tool Server:** Azure Function App hosting all 6 endpoints

**Agent:** Hosted container on Azure AI Foundry, calls tools via HTTP

---

### 3. Explore the World — Data Dashboard (3 min)

**Demo:** Open `data/dashboard.html` in browser

**Show:**
- **Overview tab:** 5 customers, 28 products, 12 orders
- **Customers tab:** 3 loyalty tiers (Platinum, Gold, Standard)
- **Orders tab:** Pick an order, show line items and fulfillment
- **Products tab:** Show categories (Electronics, Apparel, etc.)
- **Eval Scenarios tab:** 254 total scenarios (192 train, 62 validation)
  - Filter by resolution type (Refund, Exchange, Deny, etc.)
  - Show distribution charts

**Key Insight:** "These scenarios cover all edge cases — defective items, late deliveries, sale items, multi-item orders, return window boundaries."

---

### 4. Deploy an Agent (2 min)

**Demo:** Show deployment command (pre-run, just explain)

```bash
cd demo-v2
./scripts/deploy_agent.sh zava-next o4-mini
```

**Explain:**
- Script generates concrete manifest from template
- Deploys model if not present
- Deploys agent container
- Grants IAM role for model access

**Show:** Agent manifest (`agents/zava-next/agent.yaml.template`)
- Same codebase for all models
- Model selected via `AZURE_AI_MODEL_DEPLOYMENT_NAME` env var

**Result:** All 6 models deployed as separate agents

---

### 5. Invoke an Agent (3 min)

**Demo:** Live agent invocation

```bash
cd demo-v2/deploy
azd ai agent invoke \
  --agent-name zava-next-o4-mini \
  --message "I need to return the headphones from order ORD-005, they are defective"
```

**Expected Response:**
```
The agent processes your return request:
1. Retrieved order ORD-005
2. Checked delivery status
3. Confirmed defective item policy
4. Calculated refund: $149.99 (0% restocking fee for defective)
5. Submitted return authorization

Your return has been approved...
```

**Show Traces:** Open Azure AI Foundry portal
- Go to Tracing tab
- Show most recent trace
- Expand to see tool-call sequence
- Point out latency per tool call

**Key Insight:** "Notice the agent called 5 tools in the correct order. But does it always get this right? That's what we'll test in Phase 2."

---

## ✅ Success Criteria

At the end of Phase 1, verify:
- [ ] Audience understands Zava-Next's purpose
- [ ] 6-tool workflow is clear
- [ ] Data dashboard exploration was interactive
- [ ] Deployment process was demonstrated
- [ ] Live agent invocation worked
- [ ] Traces are visible in portal
- [ ] Transition to Phase 2 is set up ("But how well do base models really perform?")

---

## 📁 Files & Resources

| File | Purpose |
|------|---------|
| `demo-zava-next.md` | Complete architecture and deployment guide |
| `data/dashboard.html` | Interactive data explorer |
| `data/zava_db.json` | Mock database with all test data |
| `agents/zava-next/main.py` | Agent source code |
| `agents/zava-next/agent.yaml.template` | Agent manifest template |
| `scripts/deploy_agent.sh` | Deployment automation |
| `tools/zava-next-tools/function_app.py` | Tool server (6 endpoints) |

---

## 🐛 Common Issues

### Dashboard doesn't load
- **Fix:** Open `data/dashboard.html` directly in browser (double-click)
- Verify `dashboard_data.js` is in same directory

### Agent invocation fails
- **Check:** Agent is deployed (`azd ai agent list`)
- **Check:** MODEL deployment exists in Foundry
- **Check:** IAM role granted (agent → model)

### Traces not showing
- **Check:** Application Insights connected
- **Check:** Wait 1-2 minutes for traces to appear
- **Refresh:** Foundry portal traces tab

---

## 🔗 Next Phase

**Phase 2: Base Model Evaluations**

Now that we've seen Zava-Next work on a simple example, let's test how well base models handle 62 diverse scenarios across all edge cases.

[→ Go to Phase 2 Guide](phase2_evaluations.md)
