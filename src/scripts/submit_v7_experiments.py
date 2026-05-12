"""Upload v7 data and submit all v7 experiments."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

lab_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# Step 1: Upload v7 data files
# ============================================================
train_path = os.path.join(lab_dir, "data", "rft_v7_train.jsonl")
val_path = os.path.join(lab_dir, "data", "rft_v7_val.jsonl")

print("Uploading training file...")
train_file = client.files.create(file=open(train_path, "rb"), purpose="fine-tune")
train_id = train_file.id
print(f"  ✅ train_id = {train_id}")

print("Uploading validation file...")
val_file = client.files.create(file=open(val_path, "rb"), purpose="fine-tune")
val_id = val_file.id
print(f"  ✅ val_id = {val_id}")

print("Waiting 60 seconds for files to process...")
time.sleep(60)

# ============================================================
# Common config
# ============================================================
TOOLS = [{"name": "get_order", "server_url": "https://zava-rft-tools.azurewebsites.net/tool/get_order", "headers": {}}]

PY_SOURCE = r"""
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
    exp_amounts = re.findall(r'\$(\d+\.\d{2})', expected)
    if exp_amounts:
        out_amounts = re.findall(r'\$(\d+\.\d{2})', output_text)
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
        tool_names = [t.get("function", {}).get("name", "") for t in output_tools]
        if "get_order" in tool_names:
            score += 0.1
    
    return round(min(score, 1.0), 3)
"""

# ============================================================
# Experiment definitions
# ============================================================
experiments = [
    {
        "suffix": "zava-v7-py80-lr1-3ep",
        "grader": {"type": "python", "name": "zava_py_v2", "source": PY_SOURCE.strip(), "pass_threshold": 0.80},
        "hyperparameters": {"learning_rate_multiplier": 1.0, "n_epochs": 3, "compute_multiplier": 1.5,
                           "eval_interval": 5, "eval_samples": 10, "reasoning_effort": "medium"},
        "description": "Baseline: LR=1.0, 3ep, threshold=0.80 (35% fail)"
    },
    {
        "suffix": "zava-v7-py80-lr2-3ep",
        "grader": {"type": "python", "name": "zava_py_v2", "source": PY_SOURCE.strip(), "pass_threshold": 0.80},
        "hyperparameters": {"learning_rate_multiplier": 2.0, "n_epochs": 3, "compute_multiplier": 1.5,
                           "eval_interval": 5, "eval_samples": 10, "reasoning_effort": "medium"},
        "description": "Higher LR: LR=2.0, 3ep, threshold=0.80"
    },
    {
        "suffix": "zava-v7-py85-lr1-3ep",
        "grader": {"type": "python", "name": "zava_py_v2", "source": PY_SOURCE.strip(), "pass_threshold": 0.85},
        "hyperparameters": {"learning_rate_multiplier": 1.0, "n_epochs": 3, "compute_multiplier": 1.5,
                           "eval_interval": 5, "eval_samples": 10, "reasoning_effort": "medium"},
        "description": "Tighter threshold: LR=1.0, 3ep, threshold=0.85 (38% fail)"
    },
    {
        "suffix": "zava-v7-py80-lr1-3ep-rh",
        "grader": {"type": "python", "name": "zava_py_v2", "source": PY_SOURCE.strip(), "pass_threshold": 0.80},
        "hyperparameters": {"learning_rate_multiplier": 1.0, "n_epochs": 3, "compute_multiplier": 1.5,
                           "eval_interval": 5, "eval_samples": 10, "reasoning_effort": "high"},
        "description": "High reasoning: LR=1.0, 3ep, threshold=0.80, reasoning=high"
    },
    {
        "suffix": "zava-v7-eg70-lr1-3ep",
        "grader": {"type": "endpoint", "name": "zava_eg_v5", "url": "https://zava-rft-tools.azurewebsites.net/grade",
                   "pass_threshold": 0.70},
        "hyperparameters": {"learning_rate_multiplier": 1.0, "n_epochs": 3, "compute_multiplier": 1.5,
                           "eval_interval": 5, "eval_samples": 10, "reasoning_effort": "medium"},
        "description": "Endpoint grader: LR=1.0, 3ep, threshold=0.70 (32% fail)"
    },
]

# ============================================================
# Submit jobs (Python grader first, then endpoint)
# ============================================================
submitted = []

for exp in experiments:
    print(f"\nSubmitting: {exp['suffix']}")
    print(f"  {exp['description']}")
    
    try:
        job = client.fine_tuning.jobs.create(
            model="o4-mini",
            training_file=train_id,
            validation_file=val_id,
            suffix=exp["suffix"],
            method={"type": "reinforcement", "reinforcement": {
                "grader": exp["grader"],
                "tools": TOOLS,
                "max_episode_steps": 5,
                "hyperparameters": exp["hyperparameters"],
                "extra_body": {"trainingType": "GlobalStandard"},
            }},
        )
        print(f"  ✅ Job: {job.id} | Status: {job.status}")
        submitted.append({"job_id": job.id, "suffix": exp["suffix"], "description": exp["description"],
                         "hyperparameters": exp["hyperparameters"], "grader_type": exp["grader"]["type"],
                         "pass_threshold": exp["grader"].get("pass_threshold")})
    except Exception as e:
        print(f"  ❌ Error: {e}")
        submitted.append({"suffix": exp["suffix"], "error": str(e)})

# Save job manifest
manifest = {
    "train_file": train_id,
    "val_file": val_id,
    "train_examples": 343,
    "val_examples": 57,
    "steps_per_epoch": 85,
    "jobs": submitted
}
out_path = os.path.join(lab_dir, "results", "v7_jobs_manifest.json")
with open(out_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\n{'='*70}")
print(f"  SUBMITTED {len([j for j in submitted if 'job_id' in j])}/{len(experiments)} jobs")
print(f"  Manifest: {out_path}")
print(f"{'='*70}")
for j in submitted:
    if "job_id" in j:
        print(f"  {j['suffix']:<35} {j['job_id']}")
    else:
        print(f"  {j['suffix']:<35} FAILED: {j['error'][:50]}")