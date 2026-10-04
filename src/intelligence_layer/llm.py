import openai

from tools.registry import TOOL_SET
from intelligence_layer.llm_provider import LlmProvider


async def stream(provider: LlmProvider, context: list) -> list:
    client = openai.AsyncClient(
        base_url=provider.base_endpoint, api_key=provider.api_key
    )

    response = await client.responses.create(
        timeout=int(provider.timeout),
        model=provider.model_id,
        input=context,
        tools=TOOL_SET,
        stream=True,
    )

    return response
