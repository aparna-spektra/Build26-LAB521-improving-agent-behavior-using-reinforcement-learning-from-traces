# Hosted Agent Project Setup — Prerequisites

This guide documents how to create a properly-wired Azure AI Foundry project with hosted agents and **working traces**. This is the prerequisite before deploying Zava/Zava-Next agents.

## TL;DR — Quick Start

```bash
# 1. First-time setup (creates project, infra, App Insights)
cd demo-v2/deploy
azd ai agent init -m ../agents/simple-test/agent.manifest.yaml
azd env set enableHostedAgentVNext true
azd provision
azd deploy

# 2. Grant role (one-time, wait 3-5 min after)
INSTANCE_ID=$(azd ai agent show | grep "Instance Identity Client ID" | awk '{print $NF}')
ACCOUNT_ID=$(azd env get-value AZURE_AI_PROJECT_ID | sed 's|/projects/.*||')
az role assignment create --assignee-object-id "$INSTANCE_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" --scope "$ACCOUNT_ID"

# 3. Verify traces work
azd ai agent invoke --message "Hello"
# Check traces in Azure AI Foundry portal → Tracing tab

# 4. Deploy agents (repeat for each model)
cd demo-v2
./scripts/deploy_agent.sh zava-next o4-mini
./scripts/deploy_agent.sh zava-next gpt-4.1
./scripts/deploy_agent.sh zava gpt-4.1-mini
# ... etc
```

> ⚠️ **Enable API key auth** in Azure Portal → AI Services → Keys and Endpoint (disabled by default)

## Key Learnings

- **Use `azd provision`** to create the project. Manual ARM/portal creation misses internal wiring needed for traces.
- The platform injects `APPLICATIONINSIGHTS_CONNECTION_STRING` into containers — but only works correctly when azd provisions the App Insights connection.
- After deploying an agent, you **must grant the "Azure AI/Foundry User" role** (ID: `53ca6127-db72-4b80-b1b0-d745d6d5456d`) to the agent's instance identity.
- Role propagation takes **3–5 minutes**.
- **API key auth** is disabled by default on new resources. Enable it in Azure Portal → AI Services resource → Resource Management → Keys and Endpoint → Enable API Key Authentication.

## Prerequisites

- Azure CLI (`az`) installed and authenticated
- Azure Developer CLI (`azd`) >= 1.25.x installed
- `azd ext install azure.ai.agents` (Foundry Agents extension)
- `Owner` or `RBAC Administrator` role on your subscription
- Python 3.12+ (for running eval scripts locally)

## Repository Structure

```
demo-v2/
├── agents/              # Agent source code (reusable across deployments)
│   ├── simple-test/     # Minimal agent for validating setup
│   ├── zava/            # Single-tool RFT agent
│   └── zava-next/       # 6-tool agent
├── deploy/              # azd project root — run all azd commands here
│   ├── azure.yaml       # azd service config
│   ├── infra/           # Bicep templates (auto-generated)
│   ├── src/             # Agent code copied here during init
│   └── .azure/          # ⚠️ gitignored — per-user env state
├── data/                # Eval datasets, RFT training data
├── eval/                # Eval scripts and graders
├── tools/               # Azure Function tool servers
├── SETUP_PREREQ.md      # This file
└── README.md
```

## Python Virtual Environment

A venv is **not required for deploying agents** (they run in Docker containers). But you'll want one for running eval scripts, notebooks, or local testing:

```bash
cd demo-v2
python3 -m venv .venv
source .venv/bin/activate
pip install azure-ai-projects azure-identity openai azure-ai-evaluation httpx
```

Add `.venv/` to `.gitignore`.

## Step 1: Initialize the Project

Create a directory with your agent source and a `agent.manifest.yaml`:

Each agent directory already has an `agent.manifest.yaml`. For initial validation, use `agents/simple-test/`.

## Step 2: Initialize with azd (Interactive)

```bash
# From the deploy/ directory
cd demo-v2/deploy

# Run init — interactive, will prompt for:
#   - Azure subscription
#   - Whether to create NEW project or use existing (choose NEW)
#   - Region (choose a hosted-agent supported region)
azd ai agent init -m ../agents/simple-test/agent.manifest.yaml

# Set the hosted agent flag
azd env set enableHostedAgentVNext true
```

When prompted:
- **Subscription:** Select your subscription
- **Project:** Choose "Create a new Foundry project"
- **Location:** Pick a supported region (see below)

### Supported Regions for Hosted Agents
- North Central US ✅ (validated — traces work)
- East US 2 ✅ (agents work, traces need azd-provisioned project)
- West US / West US 3
- Norway East / Japan East / France Central

## Step 3: Provision Resources

```bash
azd provision
```

This creates (all names auto-generated):
- Resource Group (`rg-{env-name}`)
- AI Services Account
- AI Project (with system-assigned identity)
- Azure Container Registry
- Application Insights (properly connected for traces)
- Model deployment(s) specified in manifest

## Step 4: Deploy the Agent

```bash
azd deploy
```

## Step 5: Grant Role to Agent Identity

**Critical — without this, the agent will return "internal server error" on invocation.**

```bash
# Get the account-level resource ID (remove /projects/... suffix)
FOUNDRY_ID=$(azd env get-value AZURE_AI_PROJECT_ID | sed 's|/projects/.*||')

# Get the agent's instance identity
AGENT_CLIENT_ID=$(azd ai agent show | grep "Instance Identity Client ID" | awk '{print $NF}')

# Grant "Azure AI/Foundry User" role
az role assignment create \
  --assignee "$AGENT_CLIENT_ID" \
  --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
  --scope "$FOUNDRY_ID"
```

Wait **3–5 minutes** for role propagation.

## Step 6: Enable API Key Authentication

By default, new AI Services resources have API key auth disabled.

1. Go to Azure Portal → your AI Services resource
2. Navigate to **Resource Management** → **Keys and Endpoint**
3. Enable **API Key Authentication**

This is needed if you want to call the resource using API keys (e.g., from eval scripts or notebooks).

## Step 7: Test the Agent

```bash
azd ai agent invoke "Hello, what can you do?"
```

## Step 8: Verify Traces

In the Azure AI Foundry portal:
1. Open your project
2. Go to **Tracing** tab
3. You should see traces from your invocations

Or query App Insights directly:
```bash
APP_INSIGHTS=$(az resource list -g <your-rg> --resource-type "Microsoft.Insights/components" --query "[0].name" -o tsv)
az monitor app-insights query --app "$APP_INSIGHTS" -g <your-rg> \
  --analytics-query "union traces, dependencies | where timestamp > ago(15m) | summarize count() by itemType"
```

---

## Reference: What azd Creates

| Resource | Example Name | Purpose |
|----------|-------------|---------|
| Resource Group | `rg-azd-fresh-dev` | Container for all resources |
| AI Account | `ai-account-3ak6wwihwhrsi` | AI Services (models, agents) |
| AI Project | `ai-project-azd-fresh-dev` | Project with system identity |
| Container Registry | `cr3ak6wwihwhrsi.azurecr.io` | Stores agent Docker images |
| App Insights | `appi-3ak6wwihwhrsi` | Traces and telemetry |
| Model Deployment | `o4-mini` (GlobalStandard) | LLM for the agent |

## Reference: Key Environment Variables (set by azd)

```
AZURE_SUBSCRIPTION_ID      — Subscription
AZURE_RESOURCE_GROUP       — Resource group name
AZURE_LOCATION             — Region
AZURE_AI_ACCOUNT_NAME      — AI Services account name
AZURE_AI_PROJECT_NAME      — Project name
AZURE_AI_PROJECT_ID        — Full ARM resource ID of the project
FOUNDRY_PROJECT_ENDPOINT   — Data plane endpoint for the project
AZURE_CONTAINER_REGISTRY_ENDPOINT — ACR login server
AZURE_OPENAI_ENDPOINT      — OpenAI endpoint for the account
APPLICATIONINSIGHTS_CONNECTION_STRING — Full connection string (key + ingestion endpoint)
ENABLE_HOSTED_AGENTS       — "true"
enableHostedAgentVNext     — "true"
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| "internal server error" on invoke | Agent instance identity lacks permissions | Grant role `53ca6127-...` (Step 5), wait 3-5 min |
| No traces in App Insights | Project not provisioned by azd | Re-provision with `azd provision` |
| "Failed to pull container image" | ACR connection missing | azd handles this; if manual, grant AcrPull to project identity |
| Agent stuck in "creating" | Image build failed | Check `az acr task-run list` for build errors |
| "PermissionDenied" 401 from model | Same as "internal server error" | Grant role (Step 5) |
| API key auth not working | Disabled by default | Enable in Portal (Step 6) |

---

## Deploying Agents (After Project Setup)

Once the project is provisioned (Steps 1–8 above completed with `simple-test`), you can deploy Zava/Zava-Next agents using the automation scripts.

### Deploy a Single Agent

```bash
cd demo-v2
./scripts/deploy_agent.sh <agent_type> <model_id>
```

**Agent types:** `zava`, `zava-next`

**Supported models:**

| Model ID | SKU | Notes |
|----------|-----|-------|
| `o4-mini` | Standard | 50K TPM |
| `gpt-4.1` | DataZoneStandard | GlobalStandard quota often full |
| `gpt-4.1-mini` | Standard | 50K TPM |
| `gpt-4.1-nano` | GlobalStandard | — |
| `gpt-5.4` | GlobalStandard | version 2026-03-05 |
| `gpt-5.4-mini` | GlobalStandard | version 2026-03-17 |

**Examples:**
```bash
./scripts/deploy_agent.sh zava-next o4-mini     # → agent: zava-next-o4-mini
./scripts/deploy_agent.sh zava gpt-4.1          # → agent: zava-gpt-4.1
./scripts/deploy_agent.sh zava-next gpt-5.4-mini # → agent: zava-next-gpt-5.4-mini
```

### Deploy All Agents

```bash
./scripts/deploy_all.sh              # All 12 agents (6 models × 2 types)
./scripts/deploy_all.sh zava-next    # Just zava-next variants (6 agents)
./scripts/deploy_all.sh zava         # Just zava variants (6 agents)
```

### Custom Tool URLs

By default, the scripts use the deployed tool servers:
- `zava-next` → `https://zava-next-tools-omkarm.azurewebsites.net`
- `zava` → `https://zava-rft-tools-omkarm.azurewebsites.net`

Override with environment variables:
```bash
export ZAVA_NEXT_TOOL_URL="https://your-next-tools.azurewebsites.net"
export ZAVA_TOOL_URL="https://your-zava-tools.azurewebsites.net"
./scripts/deploy_all.sh
```

### How It Works

1. The script reads the **template manifest** from `agents/<type>/agent.manifest.yaml`
2. Replaces `{{MODEL_ID}}` and `{{TOOL_URL}}` placeholders with concrete values
3. Dots in model names are converted to hyphens for agent naming (e.g., `gpt-4.1` → `gpt-4-1`)
4. Copies source files + generated manifest to `.generated/<type>-<model>/`
5. **Deploys the model** if not already present (correct SKU/version auto-selected)
6. Runs `azd ai agent init -m <generated-manifest>` + `azd deploy`
7. Grants the required role to the agent's instance identity (idempotent — only needed once per project)

### Important Notes

- **`azd ai agent init` is interactive** — it will prompt for agent name, deployment type, and model. Accept the defaults; they come from the manifest.
- **`azd deploy` redeploys all agents** — this is idempotent (existing agents rebuild unchanged) but takes extra time with many agents.
- **Role grant only needed once** — after the first agent deploy, subsequent agents in the same project share the role.
- **Model deployment is automatic** — the script checks if the model exists and creates it if not.

### Naming Convention

Agents are named: `<agent_type>-<model_id>` (dots replaced with hyphens)

| Agent | Model | Purpose |
|-------|-------|---------|
| `zava-next-o4-mini` | o4-mini | Base model baseline (6-tool) |
| `zava-next-gpt-4-1` | gpt-4.1 | Compare reasoning models (6-tool) |
| `zava-next-gpt-4-1-mini` | gpt-4.1-mini | Compare reasoning models (6-tool) |
| `zava-o4-mini` | o4-mini | Base model baseline (single-tool RFT) |
| `zava-gpt-4-1` | gpt-4.1 | Compare reasoning models (single-tool RFT) |
| ... | ... | ... |

### Verifying Multi-Agent Deployments

After deploying multiple agents, verify the previous agents still work:
```bash
# List all deployed agents
azd ai agent list

# Invoke a specific agent by name
azd ai agent invoke --agent-name zava-next-o4-mini \
  --message "I need to return the headphones from order ORD-005, they are defective"
```

---

## Current Working Deployment

- **Environment:** `omi-build26-azd-env`
- **Project:** `ai-project-omi-build26-azd-env`
- **Agent:** `simple-test` (o4-mini, traces confirmed ✅)
- **Working directory:** `demo-v2/deploy/`
