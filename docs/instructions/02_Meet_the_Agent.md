# Part 2 — Meet the Agent

> [!NOTE]
> **Notebook**: `src/02-meet-the-agent.ipynb` | **Estimated time**: ~10 minutes

In this section, you'll run Zava's return-resolution agent on live customer scenarios and observe how it uses tools to fetch order data and apply complex policy rules.

## Overview

The agent works as follows:

1. A customer sends a message (e.g., "I want to return my broken drill")
2. The agent calls the `get_order` tool to look up the order details
3. The agent applies Zava's return policy to determine the resolution
4. The agent responds with the action (refund/denial/store credit/exchange) and the dollar amounts

## Step 1: Open the Notebook

> [!TIP]
> As you open a new notebook, first, click on notebook file to open it. Next, at the top of the notebook click the **Run All** command to execute the notebook. A pop up will be created, select: **Python 3.13....**, you will have successfully executed the notebook.

1. In the VS Code Explorer (`src/` folder), open **`02-meet-the-agent.ipynb`**.
2. Run the **Setup** cell at the top to reconnect to Microsoft Foundry.

> [!NOTE]
> Each notebook re-establishes its own connection to Microsoft Foundry. This is expected — run the setup cell at the top of each notebook before working through the rest.

## Step 2: Read the Zava Return Policy

Before running the agent, read through the **policy table** in the notebook. The policy is intentionally complex — this is what makes it a good candidate for RFT:

| Rule | Details |
|------|---------|
| Return windows | Standard: 30 days · Gold: 45 days · Platinum: 60 days |
| Electronics windows | Standard: 15 days · Gold: 30 days · Platinum: 45 days |
| Electronics restocking fee | Standard: 15% · Gold: 7.5% · Platinum: 0% |
| Defective items | Always free return, $0 restocking fee |
| Sale items | Final sale — no returns (except defective: store credit only) |
| Late delivery (> 2 days) | $10 credit automatically applied |

> [!TIP]
> The agent has this policy in its system prompt. The challenge is that the model must apply **multiple rules simultaneously** — for example, a defective item that is also a sale item should result in store credit, not a refund.

## Step 3: Run the Three Scenarios

The notebook includes three pre-built customer scenarios. Run each one in order and observe the agent's output.

### Scenario 1: Defective Electronics Return

A customer wants to return a broken power tool. This is a relatively straightforward case — the item is defective, so the restocking fee is waived.

**Watch for:**
- Does the agent call `get_order` before answering?
- Does it correctly waive the restocking fee for defective items?
- Are the dollar amounts correct?

### Scenario 2: Defective Sale Item

This is where it gets tricky. The item is both **on sale** (normally final sale, no returns) and **defective** (should get store credit). The model must recognize *both* flags to reach the correct resolution.

**Watch for:**
- Does the agent issue a refund, a denial, or store credit?
- The correct answer is **store credit** — not a refund, not a denial.

### Scenario 3: Exchange Request

The customer wants an exchange rather than a return. This requires computing the return amount for the original item and the cost of the replacement item.

**Watch for:**
- Does the agent correctly compute the net exchange cost?
- Does it apply the correct return window for the customer's loyalty tier?

## Step 4: Observe the Results

After running all three scenarios, take note of what the agent got right and where it made mistakes. Common issues include:

- Getting the **action** right (e.g., refund) but the **amount** wrong
- Missing a **policy interaction** (e.g., defective + sale → store credit, not refund)
- Forgetting to apply the **late delivery credit**

> [!TIP]
> These are exactly the kinds of errors that RFT can fix. The model needs to learn the precise interaction between policy rules through trial and error — which is what you'll set up in notebooks 03 and 04.

## Agent Architecture (for reference)

The agent in this lab is composed of four parts:

| Component | Description |
|-----------|-------------|
| **System prompt** | Tells the model what it is and how to apply the Zava return policy |
| **Tool definition** | The `get_order` function schema that the model can call |
| **Tool executor** | Calls the Azure Function endpoint (with a local fallback for offline use) |
| **Agent loop** | Orchestrates model → tool call → model → final response |

Click **Next** to establish a baseline and understand how the grader drives RFT learning.
