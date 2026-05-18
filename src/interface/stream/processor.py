from openai.types.responses import (
    ResponseStreamEvent,
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseReasoningItem,
)
from typing import Literal


def step(
    machine_state: Literal["started", "reasoning", "tool_call", "message"],
    event: ResponseStreamEvent,
) -> tuple[str, Literal["reasoning", "tool_call", "message"]]:
    """
    Returns back the relevant token and the next state
    in which the interface should transition to based on the event.

    With the exception of tool_call data, the tokens are small.

    - <think>
    - </think>
    - <tool_call>
    - </tool_call>
    - and standard delta values

    When a ResponseFunctionToolCall is detected, we will include all the relevant tool call data we know.
    The only thing not guaranteed is the arguments, which will be built in-flight depending on the status.
    """
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
                token += ";arguments="
        elif output_item_type == "message":
            next_state = "message"

            if machine_state == "reasoning":
                token += "</think>"
            elif machine_state == "tool_call":
                token += "</tool_call>"
    elif type == "response.reasoning_text.delta":
        token += event.delta
    elif type == "response.function_call_arguments.delta":
        token += event.delta
    elif type == "response.output_text.delta":
        token += event.delta
    elif type == "response.output_item.done":
        if event.item.type == "function_call":
            pass
        if event.item.type == "reasoning":
            pass

    return token, next_state
