"""Zava Retail Agent (Single-Tool / RFT-style) — Policy reasoning is done by the model.

Uses only get_order tool. The model applies return policy rules from its system prompt.
This matches the RFT training setup for fair comparison.
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

TOOL_URL = os.environ.get("TOOL_URL", "https://zava-rft-tools-omkarm.azurewebsites.net")

SYSTEM_PROMPT = """You are Zava's return resolution engine. Call get_order to look up order details, then apply the return policy to compute the resolution.

POLICY: Standard=30d/15d(electronics), Gold=45d/30d, Platinum=60d/45d. Electronics restocking: Std=15%, Gold=7.5%, Plat=0%. Defective=0%. Sale=final sale (defective sale→store credit). Late delivery(>2d)=$10 credit +15d extension. Lost=replacement/refund. Pending=cancellable. Opened personal care=deny unless defective.

Respond with your resolution including: action, amounts, and policy reasoning."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order",
            "description": "Look up order details including items, prices, dates, loyalty tier, and delivery status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID (e.g., ORD-003)"}
                },
                "required": ["order_id"],
            },
        },
    }
]


def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool by calling our remote FastAPI endpoint."""
    try:
        payload = {
            "arguments": json.dumps(arguments),
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


def run_agent(user_message: str, history: list = None, max_turns: int = 5) -> str:
    """Run the single-tool agent loop."""
    client = get_openai_client()
    model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1")

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

    return "I apologize, but I'm having trouble processing your request. Please try again."


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
