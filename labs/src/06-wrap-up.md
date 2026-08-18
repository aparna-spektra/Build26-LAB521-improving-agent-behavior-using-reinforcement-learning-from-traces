# Lab: Wrap Up

## 📘 Lab Scenario
In this lab, you will work through the notebook src\06-wrap-up.ipynb and execute each code cell in sequence to complete the workflow successfully.

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
import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

load_dotenv(override=True)

project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential = DefaultAzureCredential()
)
client = project_client.get_openai_client(api_key=os.environ["AZURE_OPENAI_API_KEY"])

# Replace with your job ID from notebook 04
JOB_ID = "<paste-your-job-id-here>"

job = client.fine_tuning.jobs.retrieve(JOB_ID)
print(f"Job: {job.id}")
print(f"Status: {job.status}")
print(f"Model: {job.model}")
if job.fine_tuned_model:
    print(f"\n🎉 Fine-tuned model ready: {job.fine_tuned_model}")
elif job.status == "failed":
    print(f"\n❌ Job failed. Check the Microsoft Foundry portal for details.")
else:
    print(f"\n⏳ Still running... check back later.")
```
**What this code does:**
Authenticates and configures service clients used throughout the lab.

**Before you run this cell:**
Ensure required environment variables, credentials, and files are available before running this first cell.

**Expected result/output:**
No major output is expected unless the cell includes print or display statements.

## Summary
You have completed all executable code cells for this notebook in the required order. Proceed to the next notebook only after confirming outputs match expectations and no cell errors remain.

