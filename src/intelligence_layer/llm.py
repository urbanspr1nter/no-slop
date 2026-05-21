import openai
from openai.types.responses.response_output_item import ResponseOutputItem
from tools.registry import TOOL_SET
from intelligence_layer.llm_provider import LlmProvider


def send(provider: LlmProvider, context: list) -> list[ResponseOutputItem]:
    client = openai.Client(base_url=provider.base_endpoint, api_key=provider.api_key)

    response = client.responses.create(
        model=provider.model_id, input=context, tools=TOOL_SET, timeout=provider.timeout
    )

    if response.status == "failed":
        raise ValueError("Cannot complete the request.")

    return response.output


async def stream(provider: LlmProvider, context: list) -> list:
    client = openai.AsyncClient(
        base_url=provider.base_endpoint, api_key=provider.api_key
    )

    response = await client.responses.create(
        model=provider.model_id, input=context, tools=TOOL_SET, stream=True
    )

    return response
