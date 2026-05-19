import asyncio
import openai
from openai.types.responses import (
    ResponseStreamEvent,
    ResponseReasoningItem,
    ResponseOutputMessage,
)
from tools.registry import TOOL_SET
from typing import Literal


def step(
    machine_state: Literal["started", "reasoning", "tool_call", "message"],
    event: ResponseStreamEvent,
) -> tuple[str, Literal["started", "reasoning", "tool_call", "message"]]:
    next_state: Literal["started", "reasoning", "tool_call", "message"] = machine_state
    type = event.type

    token = ""

    if type == "response.output_item.added":
        output_item_type = event.item.type

        if output_item_type == "reasoning":
            next_state = "reasoning"
            token += "<think>"

        elif output_item_type == "message":
            next_state = "message"

            if machine_state == "reasoning":
                token += "</think>"
        else:
            pass
    elif type == "response.reasoning_text.delta":
        token += event.delta
    elif type == "response.output_text.delta":
        token += event.delta
    else:
        pass

    return token, next_state


async def stream_message(client: openai.AsyncClient, context: list):
    current_state: Literal["started", "reasoning", "tool_call", "message"] = "started"

    while True:
        stream_response = await client.responses.create(
            model="gemma-4-e2b-it", tools=TOOL_SET, stream=True, input=context
        )

        async for event in stream_response:
            # print(event.to_json())

            response_item = event
            response_item_type = response_item.type

            if response_item_type == "response.completed":
                completed_items = response_item.response.output

                for completed in completed_items:
                    if completed.type == "reasoning":
                        completed_reasoning: ResponseReasoningItem = completed
                        pass
                    elif completed.type == "message":
                        completed_message: ResponseOutputMessage = completed
                        context.append(
                            {
                                "type": "message",
                                "role": completed_message.role,
                                "content": [
                                    {
                                        "type": "output_text",
                                        "text": completed_message.content[0].text,
                                    }
                                ],
                            }
                        )
                    else:
                        print(f"Unsupported completed type: {completed.type}")
            else:
                token, next_state = step(
                    machine_state=current_state, event=response_item
                )

                if "<think>" in token:
                    token = token.replace("<think>", "\n<think>\n", 1)
                elif "</think>" in token:
                    token = token.replace("</think>", "\n</think>\n", 1)

                print(token, end="", flush=True)

                if current_state == "reasoning" and next_state == "message":
                    print()

                current_state = next_state

        if current_state == "message":
            print()
            break


async def main():
    client = openai.AsyncClient(base_url="http://localhost:8000/v1", api_key="none")

    context = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi there"}],
        }
    ]

    await stream_message(client, context)


if __name__ == "__main__":
    asyncio.run(main())
