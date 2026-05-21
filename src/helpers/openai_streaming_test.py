import json
import asyncio
import openai
from openai.types.responses import (
    ResponseStreamEvent,
    ResponseReasoningItem,
    ResponseOutputMessage,
    ResponseFunctionToolCall,
)
from tools.registry import TOOL_SET
from typing import Literal
from tools.call_tool import call_tool


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
            if machine_state == "tool_call":
                token += "</tool_call>"

            next_state = "reasoning"
            token += "<think>"
        elif output_item_type == "function_call":
            if machine_state == "reasoning":
                token += "</think>"
            elif machine_state == "tool_call":
                token += "</tool_call>"

            next_state = "tool_call"
            token += "<tool_call>"

            item: ResponseFunctionToolCall = event.item
            token += f"type={item.type};call_id={item.call_id};name={item.name}"

            if item.status != "in_progress":
                token += f";arguments={item.arguments}"
                token += "</tool_call>"
            else:
                token += ";argument="
        elif output_item_type == "message":
            next_state = "message"

            if machine_state == "reasoning":
                token += "</think>"
            elif machine_state == "tool_call":
                token += "</tool_call>"
        else:
            pass
    elif type == "response.reasoning_text.delta":
        token += event.delta
    elif type == "response.function_call_arguments.delta":
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

        tool_call_queue = []

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
                    elif completed.type == "function_call":
                        completed_tool_call: ResponseFunctionToolCall = completed
                        context.append(
                            {
                                "type": completed_tool_call.type,
                                "call_id": completed_tool_call.call_id,
                                "name": completed_tool_call.name,
                                "arguments": completed_tool_call.arguments,
                            }
                        )
                        tool_call_queue.append(context[-1])
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
                elif "</tool_call>" in token:
                    token = token.replace("</tool_call>", "</tool_call>\n", 1)

                print(token, end="", flush=True)

                if (
                    current_state == "reasoning" or current_state == "tool_call"
                ) and next_state == "message":
                    print()

                current_state = next_state

        if current_state == "tool_call":
            # iterate through the tool calls
            for tool_call in tool_call_queue:
                name = tool_call["name"]

                if not tool_call["arguments"]:
                    tool_call["arguments"] = "{}"

                arguments = json.loads(tool_call["arguments"])

                result = call_tool(name, arguments)

                context.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call["call_id"],
                        "output": json.dumps(result),
                    }
                )
        elif current_state == "message":
            print()
            break


async def main():
    client = openai.AsyncClient(base_url="http://localhost:8000/v1", api_key="none")

    context = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "hi what is the square root of 289? Then tell me what is this: 7^5.",
                }
            ],
        }
    ]

    await stream_message(client, context)


if __name__ == "__main__":
    asyncio.run(main())
