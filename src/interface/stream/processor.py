from openai.types.responses import (
    ResponseStreamEvent,
)
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
        elif output_item_type == "function_call":
            token += event.item.name
            next_state = "tool_call"
        elif output_item_type == "message":
            next_state = "message"
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
