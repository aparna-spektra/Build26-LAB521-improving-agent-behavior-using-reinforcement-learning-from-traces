"""Zava Next Multi-Tool Agent — 6-tool agentic workflow for post-purchase resolution.

The model calls tools in sequence to gather info, check policy, calculate amounts,
and submit resolutions. Policy logic is in the tools, not the model.
"""

import asyncio
import json
import os

import httpx
from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
    TextResponse,
)
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

TOOL_URL = os.environ.get("TOOL_URL", "https://zava-next-tools-omkarm.azurewebsites.net")

SYSTEM_PROMPT = """\
You are Zava's Post-Purchase Resolution Desk agent. You help customers with returns, exchanges, replacements, cancellations, and shipping disputes.

## Available Tools (call in this order)
1. **get_order_details** - Retrieve order info, line items, customer loyalty tier
2. **get_fulfillment_status** - Check delivery status, late delivery, lost packages
3. **check_resolution_policy** - Verify eligibility per item (call once PER item)
4. **check_inventory** - Check stock ONLY when processing an exchange
5. **calculate_resolution** - Compute refund amounts, fees, credits
6. **submit_resolution** - Finalize the resolution (only after calculate_resolution)

## Required Workflow
1. Always start with get_order_details, then get_fulfillment_status.
2. For each item needing resolution, call check_resolution_policy with the customer's stated reason.
3. If an exchange is requested, call check_inventory for the desired SKU.
4. Call calculate_resolution with the full list of item actions.
5. Only call submit_resolution AFTER calculate_resolution confirms amounts.
6. NEVER call submit_resolution without calling calculate_resolution first.

## Return Windows (from delivery date)
| Tier      | Apparel/Home | Electronics | Personal Care      |
|-----------|-------------|-------------|--------------------|
| Standard  | 30 days     | 15 days     | 15 days (sealed)   |
| Gold      | 45 days     | 30 days     | 30 days (sealed)   |
| Platinum  | 60 days     | 45 days     | 45 days (sealed)   |

Electronics includes: headphones, keyboards, speakers, watches, kettles, lamps.

## Restocking Fees
- Apparel/home: NO restocking fee
- Electronics (non-defective): Standard 15%, Gold 7.5%, Platinum 0%
- Defective items: ALWAYS 0%

## Sale items: Final sale (no returns/exchanges); defective sale -> store credit ONLY.
## Late delivery (>2 days): $10 shipping credit per late item, return window +15 days.
## Lost packages: full replacement OR full refund; no restocking fee.
## Cancellations: only if pending or processing; full refund.
## Defective: ALWAYS eligible regardless of window/sale/category. No restocking fee.
## Personal care: cannot return once opened, unless defective.

For each item address it separately. Cite the specific policy when denying. State refund amounts clearly.

## Response Format (MANDATORY)
After your customer-facing response, you MUST append a line starting with "---" followed by a machine-readable summary.
Example:
---
Action: refund for LI-001 (reason: defective). Amount: $49.99.

Format rules:
- Approved: Action: <action> for <item_id> (reason: <reason>). Amount: $<amount>.
- Denied: Action: deny for <item_id> (reason: <denial_reason>).
- Cancelled: Action: cancel for <item_id> (reason: cancellation).
- Multiple items: one Action line per item.
- <action> must be one of: refund, exchange, replacement, store_credit, shipping_credit, cancel, deny.
- NEVER omit the --- summary block. It is required for processing.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": (
                "Retrieve order details: line items (item_id, product_name, category, "
                "sku, quantity, unit_price, discount_pct, on_sale), customer info (name, "
                "email, loyalty_tier), payment method, dates, subtotal, tax, total. "
                "Always call this first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID, e.g. 'ORD-001'"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_fulfillment_status",
            "description": (
                "Get per-item shipping/fulfillment status. Returns each item's status "
                "(processing/shipped/delivered/lost), ship_date, delivery_date, carrier, "
                "late_delivery flag, days_late, and days_since_delivery."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_resolution_policy",
            "description": (
                "Check resolution eligibility for ONE item. Returns: eligible (bool), "
                "eligible_actions, return_window_days, days_since_delivery, "
                "restocking_fee_pct, shipping_credit, special_rules, denial_reason. "
                "Call once PER item needing resolution."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "item_id": {"type": "string", "description": "The line item ID, e.g. 'LI-002'"},
                    "reason": {
                        "type": "string",
                        "description": (
                            "Customer's reason: 'defective', 'buyers_remorse', "
                            "'wrong_item', 'doesnt_fit', 'changed_mind', "
                            "'damaged_in_shipping', or 'opened_not_needed'."
                        ),
                    },
                },
                "required": ["order_id", "item_id", "reason"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": (
                "Check stock for a SKU. Returns in_stock, quantity, restock_date "
                "(if OOS), and alternative in-stock variants. "
                "Call ONLY when processing an exchange."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "description": "Product SKU, e.g. 'P007-9' or 'P003-M'"},
                },
                "required": ["sku"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_resolution",
            "description": (
                "Calculate financial details for a resolution plan. Takes a list of "
                "item actions with item_id, action (refund/exchange/replacement/"
                "store_credit/deny/shipping_credit), reason, and optionally "
                "exchange_sku. Returns per-item breakdown and totals. "
                "Always call check_resolution_policy FIRST."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "items": {
                        "type": "array",
                        "description": "List of item resolution actions",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item_id": {"type": "string"},
                                "action": {
                                    "type": "string",
                                    "enum": [
                                        "refund", "exchange", "replacement",
                                        "store_credit", "deny", "shipping_credit",
                                    ],
                                },
                                "reason": {"type": "string"},
                                "exchange_sku": {"type": "string"},
                            },
                            "required": ["item_id", "action", "reason"],
                        },
                    },
                },
                "required": ["order_id", "items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_resolution",
            "description": (
                "Submit the final resolution for processing. Returns a confirmation "
                "ID. ONLY call after calculate_resolution confirms the amounts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID"},
                    "resolution_summary": {
                        "type": "string",
                        "description": "Text summary of the resolution being submitted",
                    },
                },
                "required": ["order_id", "resolution_summary"],
            },
        },
    },
]


def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool by calling our remote FastAPI endpoint."""
    try:
        payload = {
            "arguments": arguments if isinstance(arguments, dict) else json.loads(arguments),
            "call_id": "",
            "id": "",
        }
        r = httpx.post(f"{TOOL_URL}/tool/{name}", json=payload, timeout=30)
        if r.status_code != 200:
            return f"Error: {r.status_code} - {r.text}"
        resp = r.json()
        return resp.get("output", r.text)
    except Exception as e:
        return f"Tool error: {e}"


def get_openai_client():
    """Build an OpenAI client via Foundry AIProjectClient."""
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    credential = DefaultAzureCredential()
    project_client = AIProjectClient(endpoint=endpoint, credential=credential)
    return project_client.get_openai_client()


def run_agent(user_message: str, history: list = None, max_turns: int = 12) -> str:
    """Run the multi-tool agent loop."""
    client = get_openai_client()
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "o4-mini")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    for _ in range(max_turns):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
        )
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return msg.content or ""

        messages.append(msg.model_dump())
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = call_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    return "I apologize, but I was unable to complete the resolution within the allowed number of steps."


# --- Hosted Agent Server (Responses protocol) ---

app = ResponsesAgentServerHost(options=ResponsesServerOptions(default_fetch_history_count=20))


@app.response_handler
async def handle_create(request: CreateResponse, context: ResponseContext, cancellation_signal):
    """Handle incoming responses requests."""
    current_input = await context.get_input_text()

    history = []
    try:
        prev_items = await context.get_history()
        for item in prev_items:
            if hasattr(item, "content") and item.content:
                for content in item.content:
                    if hasattr(content, "text") and content.text:
                        if hasattr(content, "type"):
                            if content.type == "input_text":
                                history.append({"role": "user", "content": content.text})
                            elif content.type == "output_text":
                                history.append({"role": "assistant", "content": content.text})
    except Exception:
        pass

    result = await asyncio.to_thread(run_agent, current_input, history)
    return TextResponse(context, request, text=result)


if __name__ == "__main__":
    app.run()
