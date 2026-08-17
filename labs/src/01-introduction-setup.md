# Lab: Introduction Setup

## 📘 Lab Scenario
In this lab, you will work through the notebook src\01-introduction-setup.ipynb and execute each code cell in sequence to complete the workflow successfully.

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
%pip install -q openai python-dotenv requests tabulate matplotlib azure-ai-projects aiohttp
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
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv(override=True)

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential = DefaultAzureCredential()
)
client = project_client.get_openai_client(api_key=os.environ["AZURE_OPENAI_API_KEY"])

# Quick connectivity check — make a simple chat completion
test = client.chat.completions.create(
    model="gpt-5-mini",
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
# Verify environment variables
required_vars = ["FOUNDRY_PROJECT_ENDPOINT","AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY"]
for var in required_vars:
    value = os.environ.get(var, "")
    if value:
        print(f"  ✅ {var} is set.")
    else:
        print(f"  ❌ {var} is NOT set! Check your .env file.")

# Verify data files exist
print("\nData files:")
data_files = ["data/rft_v7_train.jsonl", "data/rft_v7_val.jsonl",
              "results/training_metrics.csv", "results/v7_checkpoint_eval.json"]
for f in data_files:
    exists = os.path.exists(f)
    size = os.path.getsize(f) if exists else 0
    status = f"✅ {size:,} bytes" if exists else "❌ MISSING"
    print(f"  {f}: {status}")

print("\n🎉 Setup complete! Proceed to notebook 02-meet-the-agent.ipynb")
```
**What this code does:**
Loads or inspects data required for subsequent analysis or training.

**Before you run this cell:**
Run all previous cells successfully before executing this cell.

**Expected result/output:**
Successful execution without errors and values prepared for later cells.

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

