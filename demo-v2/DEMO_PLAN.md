# LAB521: Improving AI Agents with Reinforcement Learning — Demo Plan

**Session:** Build 2026 LAB521  
**Topic:** Improving AI Agent Behavior Using Reinforcement Fine-Tuning  
**Status:** Phase 2 Complete ✅ — Moving to Phase 3  
**Last Updated:** 2026-05-26

---

## 🎯 Demo Objective

Show how to improve AI agent behavior using Reinforcement Learning techniques:
1. **Establish baseline** — Deploy multi-model agents and evaluate performance
2. **Identify failure patterns** — Analyze where base models struggle
3. **Apply RFT** — Train with reinforcement learning on o4-mini
4. **Apply LoRA** — Advanced training on Qwen3-32B
5. **Measure improvement** — Compare pre- vs post-training performance

---

## 📋 Four-Phase Structure

### Phase 1: Introduction to Zava-Next Agent ✅ 
**Status:** Complete  
**Demo Time:** 10-12 minutes

#### What We'll Show:
1. **The Zava-Next Agent** — Multi-tool post-purchase resolution agent
   - 6 tools: order lookup → fulfillment → policy check → inventory → calculate → submit
   - Complex business rules (return windows, restocking fees, sale policies)
   - Handles returns, exchanges, replacements, cancellations

2. **The World** — Mock e-commerce database (`zava_db.json`)
   - 5 customers (3 loyalty tiers)
   - 28 products (4 categories)
   - 12 orders with various fulfillment states
   - 254 evaluation scenarios

3. **Data Dashboard** — Interactive visualization
   - **Demo:** Open `data/dashboard.html` in browser
   - Show customer profiles, orders, products, scenarios
   - Highlight scenario distribution and edge cases

4. **Deployment** — Azure AI Foundry hosted agents
   - **Demo:** Show deployment command
   ```bash
   ./scripts/deploy_agent.sh zava-next o4-mini
   ```
   - Show agent manifest (`agents/zava-next/agent.yaml.template`)
   - Explain: Same codebase, different models via env var

5. **Live Agent Test** — Invoke a deployed agent
   - **Demo:** Test with example scenario
   ```bash
   azd ai agent invoke --message "I need to return the headphones from order ORD-005"
   ```
   - Show tool-call sequence in traces

#### Files & Resources:
- **Guide:** `demo-zava-next.md` (architecture, deployment, scenarios)
- **Dashboard:** `data/dashboard.html` (interactive data explorer)
- **Database:** `data/zava_db.json` (all test data)
- **Agent Code:** `agents/zava-next/main.py`
- **Deployment Script:** `scripts/deploy_agent.sh`

#### Success Criteria:
- ✅ Audience understands what Zava-Next does
- ✅ 6-tool workflow is clear
- ✅ Business rules complexity is apparent
- ✅ Deployment process is demonstrated
- ✅ Traces are visible in Foundry portal

---

### Phase 2: Base Model Evaluations ✅  
**Status:** Complete  
**Demo Time:** 12-15 minutes  
**Latest Run:** zava-multi-model-eval-20260526-210056

#### What We'll Show:
1. **Evaluation Dataset** — 62 held-out validation scenarios (v2)
   - Never seen during training
   - Covers all policy dimensions
   - **Demo:** Show `data/rft_next_val.jsonl` structure

2. **Custom Grader** — Python evaluator (`zava_quality`)
   - **Scoring dimensions:**
     - Decision Correctness (50%) — Right action?
     - Financial Accuracy (30%) — Correct amounts?
     - Format Compliance (20%) — Structured output?
   - **Demo:** Walk through `eval/zava_grader_response.py`
   - Show how grader parses actions and validates results

3. **Multi-Model Evaluation** — Test all 6 base models
   - **Demo:** Run evaluation notebook
   - **Notebook:** `base_evaluations.ipynb`
   - Show how to:
     - Upload dataset to Foundry
     - Load custom grader
     - Create evaluation definition
     - Launch runs for all models
     - Monitor progress

4. **Results Analysis** — Compare model performance
   - **Demo:** Open completed Foundry eval run
   - Show results table (pass rates by model)
   - **Expected:** gpt-4-1-mini ~56.5%, o4-mini ~46%
   - Show per-criteria breakdown
   - **Document:** `eval/BASELINE_EVAL_ANALYSIS.md`

5. **Failure Pattern Analysis** — Where do models struggle?
   - **Key Finding:** "The Execution Gap"
     - Models understand intent (89% avg)
     - But fail at execution (60% avg)
     - 30% drop from understanding → doing
   - **Common errors:**
     - Decision errors (50% of failures)
     - Financial calculation errors (30%)
     - Format violations (20%)
   - **Demo:** Show example failed scenarios

6. **Model Selection for RFT** — Pick base model to improve
   - **Recommendation:** gpt-4-1-mini
   - Why: Best baseline (56.5%), reasonable cost
   - **Target:** >80% after RFT (24% improvement)

#### Files & Resources:
- **Notebook:** `notebooks/phase2_base_evaluations.ipynb` (main eval workflow)
- **Dataset:** `data/rft_next_val_v2.jsonl` (62 validation scenarios - FIXED VERSION)
- **Dataset Changelog:** `data/DATASET_CHANGELOG.md` (documents v2 fixes)
- **Grader:** `eval/zava_grader_response.py` (custom Python grader - FIXED)
- **Analysis:** `eval/BASELINE_EVAL_ANALYSIS.md` (comprehensive report)
- **Results:** `eval/eval_results_*.json` (raw data)
- **Config:** `.env` (project endpoint, API key)

#### Success Criteria:
- ✅ Audience understands evaluation workflow
- ✅ Custom grader logic is clear
- ✅ Multi-model comparison shows performance spread
- ✅ Failure patterns highlight need for RFT
- ✅ Base model selected for Phase 3
- ✅ Custom grader logic is clear
- ✅ Multi-model comparison shows performance gap
- ✅ Failure patterns are identified
- ✅ Case for RFT is established

#### Current Blockers:
- ⏳ Waiting for eval run `zava-multi-model-eval-20260526-194103` to complete
- ⏳ Grader fixes applied (removed re.compile(), added grade() function)
- ✅ .env configuration working
- ✅ Dataset upload via SDK working

---

### Phase 3: Reinforcement Fine-Tuning (RFT) 📝  
**Status:** Planned  
**Demo Time:** 10-12 minutes

#### What We'll Show:
1. **RFT Training Dataset Preparation**
   - Extract 22 failed scenarios from gpt-4-1-mini
   - Add 10-15 edge cases (passed but close to threshold)
   - Total: 35-40 training examples
   - **Demo:** Show notebook that generates training data
   - Format: JSONL with reward signals

2. **Submit RFT Job** — Azure AI Foundry
   - **Base model:** o4-mini
   - **Training data:** 35-40 examples with rewards
   - **Grader:** Full agentic grader (validates tool calls)
   - **Demo:** Submit via Foundry UI or SDK
   - Show job configuration (hyperparameters, reward model)

3. **Monitor Training** — Track progress
   - **Demo:** Show training metrics in Foundry portal
   - Loss curves, reward trends, completion estimate
   - Training typically takes: 2-4 hours

4. **Deploy Fine-Tuned Model** — As hosted agent
   - **Demo:** Deploy `zava-next-o4-mini-rft` agent
   - Point to fine-tuned model deployment
   - Same agent codebase, new model

5. **Post-RFT Evaluation** — Run same 62 scenarios
   - **Demo:** Launch evaluation on fine-tuned agent
   - Compare with baseline o4-mini results
   - **Expected improvement:** 15-25% gain
   - Show which scenario types improved most

6. **Results Comparison** — Before vs After
   - **Demo:** Side-by-side comparison table
   - Overall pass rate: 46% → 65-70%
   - Decision correctness: Most improved
   - Financial accuracy: Moderate gain
   - Format compliance: Slight gain
   - **Visualization:** Charts showing improvement by category

#### Files & Resources (To Be Created):
- **Notebook:** `01_prepare_rft_training_data.ipynb`
- **Notebook:** `02_submit_rft_job.ipynb`
- **Notebook:** `03_evaluate_rft_model.ipynb`
- **Training Data:** `eval/rft_training_examples.jsonl` (extracted failures)
- **Grader:** `eval/zava_grader_agentic.py` (full grader with tool validation)
- **Results:** `eval/rft_comparison_results.json`
- **Guide:** `docs/RFT_TRAINING.md` (detailed instructions)

#### Success Criteria:
- ✅ Training data extraction is automated
- ✅ RFT job submission is demonstrated
- ✅ Post-RFT evaluation shows improvement
- ✅ Comparison clearly shows gains
- ✅ Failure modes reduced

---

### Phase 4: LoRA Training (Qwen3-32B) 📝  
**Status:** Planned  
**Demo Time:** 8-10 minutes

#### What We'll Show:
1. **Why LoRA?** — Advanced training for open models
   - **Use case:** Fine-tune large open-source models efficiently
   - **Model:** Qwen3-32B (state-of-the-art open LLM)
   - **Technique:** LoRA (Low-Rank Adaptation) — parameter-efficient
   - **Advantage:** Train on limited compute, preserve base model

2. **Training Data** — Reuse RFT examples
   - Same 35-40 scenarios from Phase 3
   - Convert to LoRA training format
   - **Demo:** Show format conversion

3. **Submit LoRA Job** — Azure ML or Foundry
   - **Demo:** Submit training job
   - Show LoRA config (rank, alpha, target modules)
   - Explain: Training updates small adapter weights, not full model

4. **Deploy LoRA Model** — As hosted agent
   - **Demo:** Deploy `zava-next-qwen3-32b-lora` agent
   - Load base model + LoRA adapter

5. **Evaluate LoRA Model** — Run same 62 scenarios
   - **Demo:** Compare Qwen3-32B base vs LoRA fine-tuned
   - Expected: Similar or better gains than RFT

6. **Final Comparison** — All models
   - **Demo:** Show final leaderboard
   - Base models (6) vs RFT (o4-mini) vs LoRA (Qwen3-32B)
   - Highlight: Best overall performer, cost/performance tradeoffs

#### Files & Resources (To Be Created):
- **Notebook:** `04_lora_training_qwen.ipynb`
- **Notebook:** `05_evaluate_lora_model.ipynb`
- **Training Data:** `eval/lora_training_examples.jsonl`
- **Config:** `eval/lora_config.yaml`
- **Results:** `eval/final_comparison_results.json`
- **Guide:** `docs/LORA_TRAINING.md`

#### Success Criteria:
- ✅ LoRA training is explained clearly
- ✅ Qwen3-32B model is fine-tuned
- ✅ Post-LoRA evaluation shows improvement
- ✅ Final comparison shows all models
- ✅ Cost/performance tradeoffs are discussed

---

## 📁 Proposed File Organization

### Current Structure:
```
demo-v2/
├── README.md                       # ← Update with 4-phase overview
├── DEMO_PLAN.md                    # ← This file (master plan)
├── SETUP_PREREQ.md                 # Prerequisites and environment setup
├── demo-zava-next.md               # ← Phase 1 guide (keep, enhance)
├── .env                            # Project configuration (gitignored)
├── .env.example                    # Template (committed)
├── requirements.txt                # Python dependencies
│
├── agents/
│   └── zava-next/                  # Agent source code
│       ├── main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── agent.yaml.template
│
├── tools/
│   └── zava-next-tools/            # Function App (6 tools)
│       └── function_app.py
│
├── data/
│   ├── zava_db.json                # Mock database (all test data)
│   ├── dashboard.html              # ← Interactive data explorer (Phase 1)
│   ├── dashboard_data.js
│   ├── rft_next_val.jsonl          # Validation dataset (62 scenarios)
│   └── rft_next_train.jsonl        # Training dataset (343 scenarios)
│
├── eval/
│   ├── zava_grader_response.py     # ← Phase 2 grader (response-only)
│   ├── zava_grader_agentic.py      # Phase 3/4 grader (with tool validation)
│   ├── BASELINE_EVAL_ANALYSIS.md   # ← Phase 2 analysis doc
│   ├── baseline_analysis.json      # Machine-readable results
│   └── detailed_results/           # Per-model metadata
│
├── notebooks/                      # ← NEW: Organize all notebooks here
│   ├── phase2_base_evaluations.ipynb        # ← Rename from base_evaluations.ipynb
│   ├── phase3_01_prepare_rft_data.ipynb     # Extract failures for RFT
│   ├── phase3_02_submit_rft_job.ipynb       # Launch RFT training
│   ├── phase3_03_evaluate_rft.ipynb         # Eval fine-tuned model
│   ├── phase4_01_lora_training.ipynb        # LoRA on Qwen3-32B
│   └── phase4_02_final_comparison.ipynb     # All models comparison
│
├── docs/                           # ← NEW: Phase-specific guides
│   ├── phase1_introduction.md      # Phase 1 walkthrough
│   ├── phase2_evaluations.md       # Phase 2 walkthrough
│   ├── phase3_rft_training.md      # Phase 3 walkthrough
│   └── phase4_lora_training.md     # Phase 4 walkthrough
│
├── scripts/
│   ├── deploy_agent.sh             # Deploy single agent
│   └── deploy_all.sh               # Batch deploy all models
│
└── deploy/                         # azd deployment artifacts
    └── infra/                      # Bicep templates
```

---

## 🔄 Reorganization Tasks

### 1. Move and Rename Notebooks
```bash
# Create notebooks directory
mkdir -p notebooks

# Move and rename existing notebook
mv base_evaluations.ipynb notebooks/phase2_base_evaluations.ipynb

# Remove backup
rm base_evaluations.ipynb.backup
```

### 2. Create Docs Directory Structure
```bash
mkdir -p docs

# Create phase guides (templates for now)
touch docs/phase1_introduction.md
touch docs/phase2_evaluations.md
touch docs/phase3_rft_training.md
touch docs/phase4_lora_training.md
```

### 3. Update README.md
- Add 4-phase overview at the top
- Link to DEMO_PLAN.md
- Link to phase-specific guides
- Update notebook references

### 4. Enhance demo-zava-next.md
- Keep as Phase 1 reference
- Add clearer section markers
- Link to data/dashboard.html

### 5. Create Phase-Specific Guides
Each guide should include:
- **Objectives:** What we're demonstrating
- **Prerequisites:** What must be done first
- **Step-by-Step:** Detailed instructions
- **Success Criteria:** How to verify it worked
- **Files & Resources:** Where to find relevant materials
- **Common Issues:** Troubleshooting tips

---

## 📊 Demo Checklist (Per Phase)

### Phase 1 Checklist:
- [ ] All 6 agents deployed and accessible
- [ ] `data/dashboard.html` opens and displays correctly
- [ ] Sample agent invocation works (with traces)
- [ ] Screenshots/recordings captured for backup

### Phase 2 Checklist:
- [x] `.env` file configured with PROJECT_ENDPOINT
- [x] `requirements.txt` has all dependencies
- [x] Dataset uploaded to Foundry
- [x] Custom grader tested and working
- [ ] Evaluation run completed successfully (⏳ in progress)
- [ ] `BASELINE_EVAL_ANALYSIS.md` updated with final results
- [ ] Failure scenarios identified and documented
- [ ] Best base model selected for RFT

### Phase 3 Checklist:
- [ ] Training data extraction notebook created
- [ ] 35-40 training examples prepared
- [ ] Agentic grader (with tool validation) created
- [ ] RFT job submitted to Foundry
- [ ] Fine-tuned model deployed as agent
- [ ] Post-RFT evaluation completed
- [ ] Comparison results documented
- [ ] Improvement charts/visualizations created

### Phase 4 Checklist:
- [ ] LoRA training data prepared
- [ ] LoRA config validated
- [ ] Qwen3-32B base model accessible
- [ ] LoRA training job submitted
- [ ] LoRA model deployed as agent
- [ ] Post-LoRA evaluation completed
- [ ] Final comparison across all models
- [ ] Cost/performance analysis documented

---

## 🚀 Next Immediate Actions

### 1. Complete Phase 2 (Current)
- [x] Fix grader compatibility issues (no re.compile(), add grade())
- [ ] Wait for eval run `zava-multi-model-eval-20260526-194103` to complete
- [ ] Verify results match previous baseline
- [ ] Update `BASELINE_EVAL_ANALYSIS.md` with final numbers
- [ ] Screenshot completed Foundry eval run

### 2. Organize Files (Next 30 mins)
- [ ] Create `notebooks/` directory
- [ ] Move `base_evaluations.ipynb` → `notebooks/phase2_base_evaluations.ipynb`
- [ ] Create `docs/` directory structure
- [ ] Create phase guide templates
- [ ] Update README.md with 4-phase overview

### 3. Prepare for Phase 3 (Next session)
- [ ] Create `notebooks/phase3_01_prepare_rft_data.ipynb`
- [ ] Extract failed scenarios from baseline eval
- [ ] Review `eval/zava_grader_agentic.py` (full grader)
- [ ] Document RFT submission process
- [ ] Create `docs/phase3_rft_training.md` guide

---

## 📝 Notes & Decisions

### Eval Run Status (2026-05-26 19:42):
- **Run ID:** `zava-multi-model-eval-20260526-194103`
- **Status:** Running (submitted 19:41 UTC)
- **Grader fixes applied:**
  - ✅ Removed `re.compile()` calls
  - ✅ Added required `grade(sample, item)` function
- **Expected completion:** 19:56-20:01 UTC (~15-20 min total)
- **Models being evaluated:** All 6 (o4-mini, gpt-4-1, gpt-4-1-mini, gpt-4-1-nano, gpt-5-4, gpt-5-4-mini)

### Grader Evolution:
- **Phase 2:** `zava_grader_response.py` (response-only, for Foundry evals)
- **Phase 3/4:** `zava_grader_agentic.py` (full validation with tool-call checks, for RFT reward)

### Model Selection for RFT:
- **Recommended:** gpt-4-1-mini (best baseline at 56.5%)
- **Alternative:** o4-mini (if we want to show max improvement from lower baseline)

### LoRA Model Choice:
- **Qwen3-32B** — Open-source, state-of-the-art, good for LoRA demo
- Can be swapped if another open model is preferred

---

## 🎬 Demo Script Outline (50-60 minutes total)

1. **Introduction** (2 min)
   - Problem: Base models struggle with complex agentic tasks
   - Solution: Reinforcement Learning improves behavior
   - What we'll show: 4-phase journey from baseline to optimized agent

2. **Phase 1: Meet Zava-Next** (10 min)
   - Show agent, tools, world
   - Demonstrate deployment and invocation
   - Show traces

3. **Phase 2: Base Model Evaluation** (12 min)
   - Explain evaluation dataset and grader
   - Show evaluation notebook workflow
   - Review completed results
   - Analyze failure patterns
   - Make case for RFT

4. **Phase 3: RFT Training** (10 min)
   - Prepare training data from failures
   - Submit RFT job
   - Deploy fine-tuned model
   - Evaluate and show improvement

5. **Phase 4: LoRA Training** (8 min)
   - Explain LoRA advantage for open models
   - Train Qwen3-32B with LoRA
   - Evaluate and compare all models

6. **Conclusion** (3 min)
   - Final comparison across all models
   - Key takeaways
   - Resources for attendees to reproduce

7. **Q&A** (5 min)

---

**End of Plan**
