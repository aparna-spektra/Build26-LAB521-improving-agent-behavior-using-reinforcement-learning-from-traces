# Facilitator Setup Guide — Zava Agentic Fine-Tuning Lab

## Pre-work Checklist (do before the session)

### 1. Azure AI Foundry Project
- [ ] Create resource: `ignite-agenticft-lab-resource` (or similar)
- [ ] Deploy `o4-mini` (Standard, 50K TPM)
- [ ] Note the endpoint URL and API key

### 2. Deploy Tool Endpoint
```bash
# From the function_app/ directory
az appservice plan create -n zava-tools-plan -g <rg-group> --sku S2 --is-linux

az webapp create -n zava-rft-tools -g <rg-group> -p zava-tools-plan --runtime "PYTHON:3.10"
az webapp config set -n zava-rft-tools -g <rg-group> --always-on true \
  --startup-command "gunicorn function_app:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker"
az webapp update -n zava-rft-tools -g <rg-group> --set siteConfig.numberOfWorkers=3

# Deploy the code
cd function_app && zip -r ../deploy.zip . && cd ..
az webapp deployment source config-zip -n zava-rft-tools -g <rg-group> --src deploy.zip

# Verify
curl https://zava-rft-tools.azurewebsites.net/
```

### 3. Pre-run Training Jobs
Run the best experiment (v7-py80-lr1-3ep) ahead of time:
```bash
cd Zava-Ignite-RL-Lab
python scripts/submit_v7_experiments.py  # submits all 5, first one is the baseline config
```
Wait for completion (~4-6 hours), then deploy the best checkpoint:
```bash
az cognitiveservices account deployment create \
  --name <resource> --resource-group <rg-group> \
  --deployment-name rft-v7-py80-step95 \
  --model-name "<fine-tuned-model-name>:ckpt-step-95" \
  --model-version 1 --model-format OpenAI \
  --sku-capacity 50 --sku-name Standard
```

### 4. Prepare Participant Environment
Each participant needs:
- [ ] `.env` file with `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_API_KEY`
- [ ] Python 3.10+ with: `openai`, `python-dotenv`, `requests`, `matplotlib`, `tabulate`
- [ ] Clone of the lab repo (or zip with `lab_notebook.py`, `data/`, `results/`)

### 5. Pre-deploy Models
Ensure these deployments exist:
- `o4-mini` — base model (Standard, 50K TPM)
- `rft-v7-py80-step95` — best fine-tuned checkpoint (Standard, 50K TPM)

### 6. Copy Pre-run Results
Ensure these files exist in `results/`:
- `v5_py90_training_metrics.csv` — reward trajectory for plotting
- `v7_checkpoint_eval.json` — checkpoint comparison data

## Session Timeline

| Time | Section | Facilitator Notes |
|------|---------|-------------------|
| 0:00 | Setup | Help with .env issues, verify connectivity |
| 0:05 | Meet the Agent | Live demo — run 2-3 scenarios, explain tool calling |
| 0:15 | Baseline | Participants run eval — takes 5-8 min, discuss while waiting |
| 0:25 | The Grader | Explain partial credit, threshold calibration |
| 0:30 | Submit Job | Walk through config, everyone submits (jobs queue for later) |
| 0:40 | Training Results | Pre-run reward curves, checkpoint comparison |
| 0:50 | Evaluate FT Model | Run fine-tuned model, compare head-to-head |
| 1:00 | Wrap-Up | Key lessons, Q&A |

## Common Issues
- **429 rate limits**: Increase TPM quota or stagger participants
- **Tool endpoint slow**: Verify Always On is enabled, check App Service plan
- **File upload pending**: Files take 10-30s to process, the notebook has a wait loop
- **Job stays pending**: Only 1 RFT job runs at a time per resource — queue is expected