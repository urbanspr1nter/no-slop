"""Dispatch a model tool call to the registered implementation.

A tool call arrives with a ``tool_name`` and JSON-decoded ``args``. This module
looks the tool up in the registry and runs it. Every result is a normalized
envelope (see tools.helpers), and ``tool.run`` guarantees a buggy tool can never
raise out of the agent loop.
"""

from tools.helpers import err
from tools.registry import TOOLS


def call_tool(tool_name: str, tool_call_id: str = "", args: dict | None = None) -> dict:
    """Execute ``tool_name`` with ``args`` and return a normalized result envelope.

    ``tool_call_id`` is optional and passed through to tools that need it
    (e.g. to name the output log files it writes).
    """
    if not isinstance(args, dict):
        args = {} if args is None else {"value": args}

    tool = TOOLS.get(tool_name)
    if tool is None:
        return err(f"Unknown tool: {tool_name}")

    return tool.run(tool_call_id=tool_call_id, **args)
