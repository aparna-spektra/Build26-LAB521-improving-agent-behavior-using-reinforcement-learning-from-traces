#!/usr/bin/env python3
"""
Check status of Foundry evaluation runs.
Usage: python3 check_foundry_status.py
"""
import json
import requests
from azure.identity import DefaultAzureCredential

# Project details
account = "ai-account-44mf5lkxqssxm"
project = "ai-project-omi-build26-azd-env"
base_url = f"https://{account}.services.ai.azure.com/api/projects/{project}/openai"

# Load run IDs
with open('eval_run_ids.json', 'r') as f:
    eval_data = json.load(f)

eval_id = eval_data['eval_id']
runs = eval_data.get('foundry_runs', {})

# Get token
credential = DefaultAzureCredential()
token = credential.get_token("https://ai.azure.com/.default").token

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("="*80)
print("FOUNDRY EVAL STATUS")
print("="*80)

status_summary = {
    'completed': [],
    'in_progress': [],
    'failed': []
}

for model_name, run_id in runs.items():
    url = f"{base_url}/evals/{eval_id}/runs/{run_id}?api-version=2025-11-15-preview"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        status = data.get('status')
        error = data.get('error')
        
        result_counts = data.get('result_counts', {})
        total = result_counts.get('total', 0)
        passed = result_counts.get('passed', 0)
        failed = result_counts.get('failed', 0)
        
        # Categorize
        if status in ['completed', 'succeeded']:
            status_summary['completed'].append(model_name)
        elif status == 'failed':
            status_summary['failed'].append(model_name)
        else:
            status_summary['in_progress'].append(model_name)
        
        # Print status
        print(f"\n{model_name}:")
        print(f"  Status: {status}")
        print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
        
        if error:
            print(f"  Error: {error.get('message', 'Unknown error')[:100]}")
        
        # Show per-criteria results if completed
        if status in ['completed', 'succeeded']:
            per_criteria = data.get('per_testing_criteria_results', [])
            if per_criteria:
                print(f"  Per-criteria:")
                for c in per_criteria:
                    name = c.get('name', 'unknown')
                    c_passed = c.get('passed', 0)
                    c_failed = c.get('failed', 0)
                    print(f"    {name}: {c_passed} passed, {c_failed} failed")
    else:
        print(f"\n{model_name}: ERROR {response.status_code}")

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"✅ Completed: {len(status_summary['completed'])} ({', '.join(status_summary['completed']) if status_summary['completed'] else 'none'})")
print(f"⏳ In Progress: {len(status_summary['in_progress'])} ({', '.join(status_summary['in_progress']) if status_summary['in_progress'] else 'none'})")
print(f"❌ Failed: {len(status_summary['failed'])} ({', '.join(status_summary['failed']) if status_summary['failed'] else 'none'})")
print("="*80)
