# Introduction

> [!NOTE]
> This is a **75-minute** hands-on lab where you will improve AI agent behavior using reinforcement fine-tuning (RFT) on traces from a real agentic workflow.

## Learning Objectives

By the end of this lab, you should be able to:

- Understand how reinforcement fine-tuning (RFT) improves agentic tool-calling behavior without redesigning the agent
- Inspect agent execution traces and define "good behavior" using evaluation graders with partial credit scoring
- Build training data from agent runs and submit an RFT fine-tuning job to Microsoft Foundry
- Evaluate checkpoints to identify the best-performing fine-tuned model

## Resources

> [!TIP]
> You can find your Microsoft Foundry endpoint, API key, and any other credentials in the **Resources tab** provided by your facilitator.

## Lab Outline

The lab is organized into **5 notebooks**, taking you through the full RFT workflow:

1. **Introduction & Setup** — Connect to Microsoft Foundry and verify your environment
2. **Meet the Agent** — Run Zava's return-resolution agent live on real scenarios and observe its tool-calling behavior
3. **Baseline & Grader** — Evaluate the base model, understand how the grader drives RFT learning, and calibrate the pass threshold
4. **Build Data & Submit a Job** — Explore the RFT data format, craft a training example, and submit a real fine-tuning job
5. **Training Results & Evaluate** — Analyze the reward curve, compare checkpoints, and run a head-to-head evaluation of the fine-tuned model

## Business Scenario

In this lab you'll be improving an AI agent for **Zava**, a fictional DIY retailer that operates both online and in physical stores across the United States. Zava specializes in home improvement, hardware, tools, and DIY supplies.

### The Challenge

Zava's customer service team handles a high volume of **return, exchange, and dispute requests**. Each request requires the agent to:

1. Look up the customer's order via a tool call
2. Apply a complex return policy with multiple rules (loyalty tiers, product categories, sale flags, late delivery credits, restocking fees, etc.)
3. Determine the correct resolution — refund, store credit, exchange, or denial — and compute the exact dollar amounts

The base model (`o4-mini`) handles most cases correctly, but struggles with edge cases: it scores around **73%** on the validation set. The goal of this lab is to push that to **87%+** using RFT.

### Why Reinforcement Fine-Tuning?

Unlike supervised fine-tuning (SFT), RFT **does not require labeled ideal responses**. Instead:

- You provide training **prompts** and a **grader function** that scores model outputs
- During training, the model generates candidate responses and receives reward signals
- The model learns through trial and error to maximize its score on the grader

This makes RFT particularly well-suited to agentic tasks where "correctness" is defined by a business rule — not by a single golden response.

### The Grader

The grader in this lab evaluates each model response on four dimensions:

| Dimension | Weight | What it checks |
|-----------|--------|----------------|
| Correct action | 40% | Did the model choose refund / denial / store credit / exchange correctly? |
| Correct amounts | 30% | Are the dollar figures (refund, fees, credits) computed correctly? |
| Policy reasoning | 20% | Does the model cite the correct policy rules? |
| Tool usage | 10% | Did the model call `get_order` to retrieve order data? |

The grader returns a score between **0.0 and 1.0**. A **pass threshold of 0.80** is used: responses scoring ≥ 0.80 count as "passing" for the RL reward signal.

Click **Next** to set up your lab environment and get started.
