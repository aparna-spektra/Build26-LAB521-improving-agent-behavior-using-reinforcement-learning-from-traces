# Demo V2 — Tracking & Important Notes

## Architecture

### Two Agents
| Agent | Description | Tools | Tool Server |
|-------|-------------|-------|-------------|
| **Zava** | Simple 1-tool agent. Policy reasoning done by the model via system prompt. | `get_order` | `zava-tools` |
| **Zava-Next** | Advanced 6-tool agentic workflow. Policy logic in tools, not model. | `get_order_details`, `get_fulfillment_status`, `check_resolution_policy`, `check_inventory`, `calculate_resolution`, `submit_resolution` | `zava-next-tools` |

### Resource: `omi-build-demo-eus2-resource` (East US 2)
- **Foundry endpoint**: `https://omi-build-demo-eus2-resource.services.ai.azure.com/`
- **Project**: `omi-build-demo-eus2`
- **Project endpoint**: `https://omi-build-demo-eus2-resource.services.ai.azure.com/api/projects/omi-build-demo-eus2`
- **OpenAI endpoint**: `https://omi-build-demo-eus2-resource.openai.azure.com/`
- **Resource Group**: `rg-omi-build-demo`
- **Region**: East US 2 (traces work here ✅)

### Model Deployments Needed
| Deployment Name | Model |
|-----------------|-------|
| `o4-mini` | o4-mini-2025-04-16 |
| `gpt-4.1` | gpt-4.1 |
| `gpt-4.1-mini` | gpt-4.1-mini |
| `gpt-4.1-nano` | gpt-4.1-nano |
| `gpt-5.4-mini` | gpt-5.4-mini |
| `gpt-5.4` | gpt-5.4 |

### Agent Naming Convention
- Zava agents: `zava-{model}` (e.g., `zava-o4-mini`, `zava-gpt-41`)
- Zava-Next agents: `zava-next-{model}` (e.g., `zava-next-o4-mini`, `zava-next-gpt-41`)

---

## Deployment Checklist

- [ ] Deploy model deployments on new resource
- [ ] Deploy `zava-tools` Function App (1 tool: get_order)
- [ ] Deploy `zava-next-tools` Function App (6 tools)
- [ ] Deploy Zava agents (all models)
- [ ] Deploy Zava-Next agents (all models)
- [ ] Verify tracing works on new resource
- [ ] Upload eval dataset
- [ ] Run evals for Zava agents
- [ ] Run evals for Zava-Next agents
- [ ] Submit RFT job (once evals confirm baseline)

---

## Important References

### NCUS Resource (existing, traces broken)
- Resource: `omi-build-demo-ncus`
- Project endpoint: `https://omi-build-demo-ncus.services.ai.azure.com/api/projects/omi-build-demo-ncus`
- Working agents: `zava-rft-o4-mini`, `zava-next-o4-mini`, etc.
- Eval run: `zava-next-agent-eval` (baseline results)
- RFT job: `ftjob-1839d286a0654e459697cd02cb8eb9a4` (pausing at step 10)

### Old EUS2 Resource (messy, being replaced)
- Resource: `omi-build-demo`
- Issues: zava-next code was pushed as new version on zava agents, mixed naming
- RFT job: `ftjob-eaa457e595b7472d97e41a19e0f26731` (running with correct config)

### Tool Servers (existing, reusable)
- `https://zava-rft-tools-omkarm.azurewebsites.net` — Zava (1 tool)
- `https://zava-next-tools-omkarm.azurewebsites.net` — Zava-Next (6 tools)
- Both have autoscale enabled

### Fine-tuned Models (for later)
- `zava-rft-o4-mini-ft` — RFT fine-tuned o4-mini (on NCUS)
- `zava-rft-qwen3-32b-ft` — Fine-tuned Qwen3-32B from Loom (on NCUS)

---

## NCUS Eval Results (Zava-Next, baseline)
| Model | Pass Rate |
|-------|-----------|
| gpt-5.4-mini | 63% 🥇 |
| o4-mini | 45% |
| gpt-4.1 | 32% |
| gpt-4.1-mini | 31% |
| gpt-5.4 | 18% |
| gpt-4.1-nano | 18% |

---

## Key Learnings / Gotchas

1. **Traces only work in EUS2**, not NCUS (region limitation or config issue)
2. **Hosted agents cannot be invoked via REST API** — only through Foundry eval system (UI) or within eval runs
3. **azd routes agents based on ACR connection**, not the FOUNDRY_PROJECT_ENDPOINT
4. **Model deployment names**: EUS2 uses dots (`gpt-4.1`), NCUS uses hyphens (`gpt-4-1`)
5. **Tool server API format**: POST `{TOOL_URL}/tool/{name}` with body `{"arguments": {...}}`
6. **RFT tools config** must include `server_url` for each tool + `max_episode_steps: 12`
7. **FOUNDRY_PROJECT_ENDPOINT** is a reserved env var — platform injects it automatically
8. **Eval grader model** must be a real model deployment, not an agent name

---

## Milestone: Fresh azd-Provisioned Project (2026-05-26)

### What Worked
- `azd provision` creates a fully-wired project with working traces
- Agent invocation works after granting "Azure AI/Foundry User" role (53ca6127-db72-4b80-b1b0-d745d6d5456d) to agent instance identity
- Traces confirmed: 527 traces + 28 dependencies visible in App Insights

### Key Findings
1. **Manual project creation doesn't support traces** — the container sandbox blocks outbound to App Insights ingestion endpoint. azd-provisioned projects route traces internally.
2. **Role grant is mandatory** — each agent's instance identity needs the Foundry User role on the account scope. Takes 3-5 min to propagate.
3. **API key auth disabled by default** — must enable in portal for API key access.
4. **APPLICATIONINSIGHTS_CONNECTION_STRING** — azd sets the FULL connection string (with ingestion endpoint). Manual setup only injected the instrumentation key, which broke azure-monitor-opentelemetry.

### Current Working Project
- **Env:** `azd-fresh-dev` (at `/tmp/azd-fresh`)
- **Region:** North Central US
- **Account:** `ai-account-3ak6wwihwhrsi`
- **Project:** `ai-project-azd-fresh-dev`
- **Agent:** `simple-agent` (o4-mini) — tested and traces working

### Next Steps
- Deploy zava-next agent with 6 tools to this project
- Verify multi-tool traces
- Deploy remaining base models
- Run evals
