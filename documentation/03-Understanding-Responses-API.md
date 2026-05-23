# Understanding Responses API

Who knew such a nice UX change could bring so much complication?

## Chat Completions vs Responses API

The Responses API uses a different message structure than the older Chat Completions API.

chat completions
```json
{
    "role": "user",
    "content": "hi there"
}

{
    "role": "assistant",
    "content": "i am doing well"
}
```

responses api
```json
{
    "type": "message",
    "role": "user",
    "content": [
        {
            "type": "input_text",
            "text": "hi there"
        }
    ]
}

{
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "output_text",
            "text": "i am doing well"
        }
    ]
}
```

## llama.cpp Quirk

OpenAI is less strict with the `/v1/responses` API, ironically. The simple Chat Completions format above would work in many contexts on OpenAI's servers. However, `llama.cpp` has stricter adherence to the Responses API — if any message in your context is missing a valid `type`, it will blow up with a 400 error.

The solution: build your entire context using the Responses API format shown above, where every message has a `type` field and content is an array of typed content objects.

## Streaming Responses

Minimal code example:
```python
import asyncio

from openai import AsyncOpenAI
from tools.registry import TOOL_SET

MODEL = "gemma-4-e4b"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"

async def main(message: str):
    client = AsyncOpenAI(base_url=BASE_API_ENDPOINT, api_key="none")
    response = await client.responses.create(
        model=MODEL,
        tools=TOOL_SET,
        stream=True,
        input=[{"role": "user", "content": message}],
    )

    async for data in response:
        print(data.to_json())


asyncio.run(main())
```

## Useful Events

These are the events we will need to check during streaming:

Types:
- `response.output_item.added`
- `response.reasoning_text.delta`
- `response.function_call_arguments.delta`
- `response.output_text.delta`
- `response.output_item.done`
- `response.completed` — Very useful. Will contain the real reasoning, tool call and message data.
