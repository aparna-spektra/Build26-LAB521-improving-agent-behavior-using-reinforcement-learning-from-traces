import asyncio
import os

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
    TextResponse,
)
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

SYSTEM_PROMPT = "You are a helpful assistant. Respond briefly."

credential = DefaultAzureCredential()
endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "o4-mini")

app = ResponsesAgentServerHost(options=ResponsesServerOptions())

@app.response_handler
async def handle_create(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
):
    user_input = await context.get_input_text()
    
    client = AIProjectClient(endpoint=endpoint, credential=credential)
    openai_client = client.get_openai_client()
    
    response = openai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ],
        max_completion_tokens=200
    )
    
    return TextResponse(context, request, text=response.choices[0].message.content)

if __name__ == "__main__":
    app.run()
