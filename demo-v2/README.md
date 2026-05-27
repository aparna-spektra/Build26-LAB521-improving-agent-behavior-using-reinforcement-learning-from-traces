# LAB521: Improving AI Agents with Reinforcement Learning

**Microsoft Build 2026 Lab Session**

This demo shows how to improve AI agent behavior using Reinforcement Learning techniques. We start with a multi-tool agent (Zava-Next) that struggles with complex business rules, then progressively improve it using RFT (cloud models) and LoRA (open models).

## 📖 Demo Plan

**[→ Read the Complete Demo Plan](DEMO_PLAN.md)** — Master plan with all 4 phases

### Four-Phase Journey:

1. **[Phase 1: Introduction](docs/phase1_introduction.md)** (10-12 min)
   - Meet the Zava-Next agent (6 tools, complex policies)
   - Explore the world (data dashboard, 254 scenarios)
   - Deploy and test agents
   - ✅ Complete

2. **[Phase 2: Base Evaluations](docs/phase2_evaluations.md)** (12-15 min)
   - Create custom Python grader (zava_quality)
   - Run multi-model evaluations (6 base models)
   - Analyze failure patterns ("The Execution Gap")
   - Select model for RFT training
   - ✅ Complete

3. **[Phase 3: RFT Training](docs/phase3_rft_training.md)** (10-12 min)
   - Extract training data from failures
   - Submit RFT job on Azure AI Foundry
   - Deploy fine-tuned model
   - Show 15-25% improvement
   - 🔄 Next

4. **[Phase 4: LoRA Training](docs/phase4_lora_training.md)** (8-10 min)
   - Train Qwen3-32B with LoRA adapters
   - Compare RFT vs LoRA approaches
   - Final results across all models
   - 📝 Planned

---

## 🚀 Quick Start

### Prerequisites
See **[SETUP_PREREQ.md](SETUP_PREREQ.md)** for environment setup.

### Current Phase: Phase 3 (RFT Training)
```bash
# Phase 2 is complete with fixed dataset and grader
# See: PHASE2_COMPLETION_SUMMARY.md for details

# For Phase 3 - RFT Training:
# 1. Extract failures from baseline evaluations
# 2. Prepare RFT training data
# 3. Submit RFT job
# 4. Evaluate fine-tuned model

# See docs/phase3_rft_training.md for walkthrough
```

---

## Folder Layout

```
demo-v2/
├── DEMO_PLAN.md          # Complete 4-phase demo plan
├── README.md             # This file
├── SETUP_PREREQ.md       # Prerequisites and environment setup
├── TRACKING.md           # Technical notes and deployment details
├── .env                  # Project configuration (gitignored)
├── .env.example          # Configuration template
├── requirements.txt      # Python dependencies
│
├── docs/                 # Phase-specific guides
│   ├── phase1_introduction.md    # Phase 1 walkthrough
│   ├── phase2_evaluations.md     # Phase 2 walkthrough
│   ├── phase3_rft_training.md    # Phase 3 walkthrough (planned)
│   └── phase4_lora_training.md   # Phase 4 walkthrough (planned)
│
├── notebooks/            # Demo notebooks (organized by phase)
│   ├── phase2_base_evaluations.ipynb        # Multi-model eval workflow
│   ├── phase3_01_prepare_rft_data.ipynb     # Extract training data (planned)
│   ├── phase3_02_submit_rft_job.ipynb       # Launch RFT training (planned)
│   ├── phase3_03_evaluate_rft.ipynb         # Eval fine-tuned model (planned)
│   ├── phase4_01_lora_training.ipynb        # LoRA training (planned)
│   └── phase4_02_final_comparison.ipynb     # All models comparison (planned)
│
├── agents/
│   └── zava-next/        # Advanced 6-tool agent
│       ├── main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── agent.yaml.template
│
├── tools/
│   └── zava-next-tools/  # Function App: 6 tool endpoints
│       └── function_app.py
│
├── eval/
│   ├── zava_grader_response.py       # Response-only grader (Phase 2)
│   ├── zava_grader_agentic.py        # Full grader with tool validation (Phase 3/4)
│   ├── BASELINE_EVAL_ANALYSIS.md     # Comprehensive analysis report
│   ├── baseline_analysis.json        # Machine-readable results
│   └── detailed_results/             # Per-model metadata
│
├── data/
│   ├── zava_db.json          # Mock database (all test data)
│   ├── dashboard.html        # Interactive data explorer
│   ├── dashboard_data.js
│   ├── rft_next_train.jsonl  # Training dataset (343 scenarios)
│   └── rft_next_val.jsonl    # Validation dataset (62 scenarios)
│
├── scripts/
│   ├── deploy_agent.sh       # Deploy single agent
│   └── deploy_all.sh         # Batch deploy all models
│
└── deploy/               # azd deployment artifacts
    └── infra/            # Bicep templates
```

## Folder Layout

See above for complete file structure organized by phase.

## The Zava-Next Agent

## The Zava-Next Agent

**Purpose:** Multi-tool AI agent for post-purchase resolution (returns, exchanges, replacements)

**The 6 Tools:**
1. `get_order_details` — Retrieve order info
2. `get_fulfillment_status` — Check delivery status  
3. `check_resolution_policy` — Verify eligibility
4. `check_inventory` — Check stock for exchanges
5. `calculate_resolution` — Compute refunds/fees
6. `submit_resolution` — Finalize action

**Business Rules:**
- Return windows by loyalty tier (Standard/Gold/Platinum)
- Restocking fees (0-15% by tier and category)
- Sale item policies (final sale unless defective)
- Late delivery credits ($10 + extended window)
- Multi-item order handling

**Why this is hard for base models:**
- Multi-step orchestration required
- Complex policy logic
- Precise financial calculations
- Structured output format

**[→ See complete agent documentation](demo-zava-next.md)**

---

## Current Status

**Phase 2 In Progress:**
- ✅ 6 agents deployed (all base models)
- ✅ Custom grader created and validated
- ✅ Dataset uploaded to Azure AI Foundry
- ⏳ Evaluation run in progress: `zava-multi-model-eval-20260526-194103`
- ⏳ Expected completion: 19:56-20:01 UTC

---

## Key Resources

| Resource | Description |
|----------|-------------|
| **[DEMO_PLAN.md](DEMO_PLAN.md)** | Complete 4-phase demo plan |
| **[Data Dashboard](data/dashboard.html)** | Interactive scenario explorer |
| **[Phase 1 Guide](docs/phase1_introduction.md)** | Agent introduction walkthrough |
| **[Phase 2 Guide](docs/phase2_evaluations.md)** | Evaluation workflow (current) |
| **[Baseline Analysis](eval/BASELINE_EVAL_ANALYSIS.md)** | Performance analysis report |
| **[demo-zava-next.md](demo-zava-next.md)** | Complete agent documentation |

---

## Deployment

For detailed deployment instructions, see **[demo-zava-next.md](demo-zava-next.md#deploying-zava-next)**

Quick deployment:

Quick deployment:

```bash
cd demo-v2
./scripts/deploy_agent.sh zava-next o4-mini
```

**All deployed agents:**
- `zava-next-o4-mini` ✅
- `zava-next-gpt-4-1` ✅
- `zava-next-gpt-4-1-mini` ✅
- `zava-next-gpt-4-1-nano` ✅
- `zava-next-gpt-5-4` ✅
- `zava-next-gpt-5-4-mini` ✅

**Project:** ai-project-omi-build26-azd-env  
**Account:** ai-account-44mf5lkxqssxm  
**Region:** North Central US

---

