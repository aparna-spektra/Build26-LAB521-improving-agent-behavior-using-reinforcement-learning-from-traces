# Base Model Evaluation

Evaluate base models directly using Azure AI Foundry's evaluation API.

## Purpose

Test base models **without deploying agents** to:
- Compare pure model capability vs agent-wrapped performance
- Identify best base models for the task
- Understand what value the agent layer adds
- Faster iteration (no deployment required)

## Approach

Use **Azure AI Foundry's base model evaluation API** to run evaluations with:
- System prompt provided inline
- Tools configured in the evaluation request
- Same dataset as Phase 2 (rft_next_val_v2.jsonl)
- Same grader as Phase 2 (zava_grader_response.py)

## Models to Test

1. **o4-mini-2025-04-16** - Reasoning model
2. **gpt-4-1** - Standard
3. **gpt-4-1-mini** - Small/fast
4. **gpt-4-1-nano** - Tiny/fastest
5. **gpt-5-4** - Latest generation
6. **gpt-5-4-mini** - Latest small

Total: 6 models × 62 scenarios = 372 evaluations

## Files

- **notebooks/base_model_evaluation.ipynb** - Main evaluation notebook
- **system_prompt.md** - System prompt for base models
- **results/** - Evaluation results (JSON)
- **analysis/** - Comparison analysis

## Usage

1. Open `notebooks/base_model_evaluation.ipynb`
2. Update API calls based on Foundry documentation
3. Run evaluation submission
4. Monitor progress in Foundry portal
5. Retrieve and analyze results

## Comparison with Phase 2

Phase 2 tested **deployed agents**:
- Agent handles system prompt injection
- Agent manages tool calling
- Tests full agent infrastructure

This tests **base models directly**:
- We provide system prompt in request
- We configure tools in request
- Tests pure model capability

**Key question:** Does agent deployment help or hurt performance?

## API Documentation Needed

This framework needs the specific Foundry API for base model evaluation:
- How to submit evaluation with system prompt + tools?
- How to specify multiple base models?
- How to monitor and retrieve results?

Check Azure AI Foundry documentation for the correct API.
