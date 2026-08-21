import asyncio
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
    """Core loop: stream a model response, execute any tool calls, feed the
    results back into context, repeat until a final message.

    Rendering is pluggable. When ``renderer`` (a callable taking plain dict
    events) is set, events are pushed to it instead of the legacy stdout
    ``render`` path. The curses TUI (interface.curses_tui) installs its hook
    here; headless and plain-terminal runs keep the legacy prints.
    """

    def __init__(self, config: Config, session_id: str | None = None):
        self._session = Session(session_id)

        self._context_manager = ContextManager()
        if len(self._session.get_context()):
            self._context_manager.set_context(self._session.get_context())

        self._intelligence = Intelligence(config)

        # Optional event sink: callable(event: dict) -> None, invoked from
        # the agent's async context. Event contract documented in
        # interface.curses_tui.
        self.renderer = None

    @property
    def session_id(self) -> str:
        return self._session.id

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

    # -- renderer event helpers ---------------------------------------------

    def _emit(self, event: dict):
        if self.renderer is not None:
            self.renderer(event)

    def _emit_delta(
        self,
        prev_state: Literal["started", "reasoning", "tool_call", "message"],
        next_state: Literal["started", "reasoning", "tool_call", "message"],
        token: str,
        event,
        streamed_calls: set,
        seen: dict,
    ):
        """Translate a processor (token, next_state) step into renderer
        events. ``streamed_calls`` tracks call ids reported via the stream so
        the completed event can skip duplicates; ``seen`` tracks whether
        reasoning/message content has streamed at all."""
        if next_state == "tool_call":
            item = getattr(event, "item", None)
            call_id = getattr(item, "call_id", "") or ""
            name = getattr(item, "name", None) or token
            if prev_state != "tool_call":
                self._emit(
                    {
                        "type": "tool_call",
                        "call_id": call_id,
                        "name": name,
                        "arguments": "",
                    }
                )
                if call_id:
                    streamed_calls.add(call_id)
            elif token:
                self._emit(
                    {
                        "type": "tool_call_args_delta",
                        "call_id": call_id,
                        "text": token,
                    }
                )
        elif next_state == "reasoning":
            if token:
                self._emit({"type": "reasoning_delta", "text": token})
                seen["reasoning"] = True
        elif next_state == "message":
            if token:
                self._emit({"type": "message_delta", "text": token})
                seen["message"] = True

    async def step(self, message: str, headless: bool = False):
        self._context_manager.build_context(message)

        current_state: Literal["started", "reasoning", "tool_call", "message"] = (
            "started"
        )

        if not headless:
            if self.renderer is not None:
                self._emit({"type": "user", "text": message})
            else:
                self.render(message, "user", "started", "message")

        try:
            while True:
                self._emit({"type": "response_start"})

                stream_response = await self._intelligence.send_message(
                    self._context_manager.get_context(), should_stream=True
                )

                tool_call_queue = []
                streamed_calls: set = set()
                seen = {"reasoning": False, "message": False}

                async for event in stream_response:
                    # print(event.to_json())

                    response_item = event
                    response_item_type = response_item.type

                    if response_item_type == "response.completed":
                        completed_items = response_item.response.output

                        for completed in completed_items:
                            if completed.type == "reasoning":
                                completed_reasoning: ResponseReasoningItem = completed
                                if (
                                    self.renderer is not None
                                    and not seen["reasoning"]
                                ):
                                    text = self._reasoning_text(completed_reasoning)
                                    if text:
                                        self._emit(
                                            {"type": "reasoning_delta", "text": text}
                                        )
                            elif completed.type == "function_call":
                                completed_tool_call: ResponseFunctionToolCall = (
                                    completed
                                )
                                self._context_manager.append_context(
                                    {
                                        "type": completed_tool_call.type,
                                        "call_id": completed_tool_call.call_id,
                                        "name": completed_tool_call.name,
                                        "arguments": completed_tool_call.arguments,
                                    }
                                )
                                tool_call_queue.append(self._context_manager.latest())
                                if (
                                    self.renderer is not None
                                    and completed_tool_call.call_id
                                    not in streamed_calls
                                ):
                                    self._emit(
                                        {
                                            "type": "tool_call",
                                            "call_id": completed_tool_call.call_id,
                                            "name": completed_tool_call.name,
                                            "arguments": completed_tool_call.arguments
                                            or "",
                                        }
                                    )
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
                                if (
                                    self.renderer is not None
                                    and not seen["message"]
                                ):
                                    self._emit(
                                        {
                                            "type": "message_delta",
                                            "text": completed_message.content[0].text,
                                        }
                                    )
                            else:
                                if self.renderer is not None:
                                    self._emit(
                                        {
                                            "type": "system",
                                            "text": f"unsupported completed type: {completed.type}",
                                        }
                                    )
                                else:
                                    print(
                                        f"Unsupported completed type: {completed.type}"
                                    )
                    else:
                        token, next_state = _step(
                            machine_state=current_state, event=response_item
                        )

                        if self.renderer is not None:
                            self._emit_delta(
                                current_state,
                                next_state,
                                token,
                                response_item,
                                streamed_calls,
                                seen,
                            )
                        else:
                            self.render(token, "assistant", current_state, next_state)

                        current_state = next_state

                if current_state == "tool_call":
                    # iterate through the tool calls
                    for tool_call in tool_call_queue:
                        name = tool_call["name"]
                        id = tool_call["call_id"]

                        if not tool_call["arguments"]:
                            tool_call["arguments"] = "{}"

                        arguments = json.loads(tool_call["arguments"])

                        # tools can be slow (shell, web); run off the loop
                        # so the TUI stays responsive
                        result = await asyncio.to_thread(
                            call_tool, tool_name=name, tool_call_id=id, args=arguments
                        )

                        self._context_manager.append_context(
                            {
                                "type": "function_call_output",
                                "call_id": tool_call["call_id"],
                                "output": json.dumps(result),
                            }
                        )

                        if self.renderer is not None:
                            self._emit(
                                {
                                    "type": "tool_result",
                                    "call_id": id,
                                    "name": name,
                                    "ok": result.get("status") == "ok",
                                    "result": result.get("result"),
                                    "message": result.get("message"),
                                }
                            )
                elif current_state == "message":
                    break

            if self.renderer is not None:
                self._emit({"type": "turn_complete"})
            else:
                print("\n")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            if self.renderer is not None:
                self._emit({"type": "error", "text": f"{type(e).__name__}: {e}"})
                self._emit({"type": "turn_complete"})
            else:
                raise

    @staticmethod
    def _reasoning_text(item: ResponseReasoningItem) -> str:
        """Best-effort plain text of a completed reasoning item (used only
        when the reasoning was not streamed as deltas)."""
        parts = []
        if item.content:
            parts.append(str(item.content))
        for summary in item.summary or []:
            text = getattr(summary, "text", None)
            if text:
                parts.append(str(text))
        return "\n".join(p for p in parts if p)
