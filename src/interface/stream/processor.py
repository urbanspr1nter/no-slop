from openai.types.responses import (
    ResponseStreamEvent,
    ResponseFunctionToolCall,
)
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
