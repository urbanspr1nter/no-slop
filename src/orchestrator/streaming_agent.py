import json
from context_management.context_manager import ContextManager
from intelligence_layer.intelligence import Intelligence
from tools.call_tool import call_tool
from config.loader import Config
from interface.stream.processor import step as _step
from typing import Literal
from openai.types.responses import (
    ResponseStreamEvent,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseReasoningItem,
)


class StreamingAgent:
    def __init__(self, config: Config):
        self._context_manager = ContextManager()
        self._intelligence = Intelligence(config)

    def set_system_prompt(self, sys_prompt: str):
        self._context_manager.set_sys_prompt(sys_prompt)

    async def step(self, message: str):
        self._context_manager.build_context(message)

        current_state: Literal["started", "reasoning", "tool_call", "message"] = (
            "started"
        )
        while True:
            response = await self._intelligence.send_message(
                self._context_manager.get_context(), should_stream=True
            )

            tool_call_queue = []

            async for data in response:
                response_item = data
                response_item_type = response_item.type

                if response_item_type == "response.completed":
                    completed_items = response_item.response.output

                    for completed in completed_items:
                        if completed.type == "reasoning":
                            completed_reasoning: ResponseReasoningItem = completed
                            # print(completed_reasoning.content[0].text)
                        elif completed.type == "function_call":
                            completed_tool_call: ResponseFunctionToolCall = completed
                            self._context_manager.append_context(
                                {
                                    "type": completed_tool_call.type,
                                    "call_id": completed_tool_call.call_id,
                                    "name": completed_tool_call.name,
                                    "arguments": completed_tool_call.arguments,
                                }
                            )
                            tool_call_queue.append(self._context_manager.latest())
                        elif completed.type == "message":
                            completed_message: ResponseOutputMessage = completed
                            self._context_manager.append_context(
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
                            raise ValueError(
                                f"Unknown type when processing response.completed event: {completed.type}"
                            )
                else:
                    token, next_state = _step(
                        machine_state=current_state, event=response_item
                    )
                    if "<think>" in token:
                        token = token.replace("<think>", "\n<think>\n", 1)
                    elif "</think>" in token:
                        token = token.replace("</think>", "\n</think>\n", 1)
                    elif "</tool_call>" in token:
                        token = token.replace("</tool_call>", "</tool_call>\n", 1)

                    print(token, end="", flush=True)

                    # We are starting a brand new message block
                    if (
                        current_state == "reasoning" or current_state == "tool_call"
                    ) and next_state == "message":
                        print()
                    current_state = next_state

            # print(context)

            if current_state == "tool_call":
                # iterate through the tool calls
                for tool_call in tool_call_queue:
                    name = tool_call["name"]

                    if not tool_call["arguments"]:
                        tool_call["arguments"] = "{}"

                    arguments = json.loads(tool_call["arguments"])

                    result = call_tool(name, arguments)

                    self._context_manager.append_context(
                        {
                            "type": "function_call_output",
                            "call_id": tool_call["call_id"],
                            "output": json.dumps(result),
                        }
                    )
            elif current_state == "message":
                print()
                break
