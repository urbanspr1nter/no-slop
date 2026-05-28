import json
from context_management.context_manager import ContextManager
from intelligence_layer.intelligence import Intelligence
from tools.call_tool import call_tool
from config.loader import Config
from interface.stream.processor import step as _step
from typing import Literal
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseReasoningItem,
)
from sessions.session import Session


class StreamingAgent:
    def __init__(self, config: Config, session_id: str | None = None):
        self._session = Session(session_id)

        self._context_manager = ContextManager()
        if len(self._session.get_context()):
            self._context_manager.set_context(self._session.get_context())

        self._intelligence = Intelligence(config)

    def set_system_prompt(self, sys_prompt: str):
        self._context_manager.set_sys_prompt(sys_prompt)

    def save_session(self):
        self._session.save(self._context_manager.get_context())

    def get_context(self):
        return self._context_manager.get_context()

    def render(
        self,
        text: str,
        turn: Literal["system", "user", "assistant"],
        previous_state: Literal["started", "reasoning", "tool_call", "message"],
        state: Literal["started", "reasoning", "tool_call", "message"],
    ):
        if turn == "system":
            print(f"<system>{text}</system>")
            return

        if previous_state != state:
            if previous_state == "reasoning":
                print("\n</think>\n", flush=True)
            elif previous_state == "tool_call":
                print("</tool_call>\n", flush=True)

            if state == "message":
                if turn == "user":
                    print("[user]")
                    print(text)
                    print()
                elif turn == "assistant":
                    print("[assistant]")
            elif state == "reasoning":
                print("<think>\n", end="", flush=True)
            elif state == "tool_call":
                print(f"<tool_call>fn:{text}:", end="", flush=True)
        else:
            # Same state, just print token
            print(text, end="", flush=True)

    async def step(self, message: str):
        self._context_manager.build_context(message)

        current_state: Literal["started", "reasoning", "tool_call", "message"] = (
            "started"
        )

        self.render(message, "user", "started", "message")

        while True:
            stream_response = await self._intelligence.send_message(
                self._context_manager.get_context(), should_stream=True
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
                            print(f"Unsupported completed type: {completed.type}")
                else:
                    token, next_state = _step(
                        machine_state=current_state, event=response_item
                    )

                    self.render(token, "assistant", current_state, next_state)

                    current_state = next_state

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
                break

        print("\n")
