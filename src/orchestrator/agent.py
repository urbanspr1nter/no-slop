import json
from context_management.context_manager import ContextManager
from intelligence_layer.intelligence import Intelligence
from tools.call_tool import call_tool


class Agent:
    def __init__(self):
        self._context_manager = ContextManager()
        self._intelligence = Intelligence()

    def set_system_prompt(self, sys_prompt: str):
        self._context_manager.set_sys_prompt(sys_prompt)

    def step(self, message: str):
        self._context_manager.build_context(message)

        result = self._intelligence.send_message(self._context_manager.get_context())

        response_text = ""
        while True:
            self._context_manager.extend(result)

            is_tool_call = False

            for item in result:
                if item.type == "function_call":
                    is_tool_call = True
                else:
                    is_tool_call = False

                if item.type == "message":
                    output_text = ""
                    for block in item.content:
                        output_text += block.text
                    response_text += output_text
                elif item.type == "reasoning":
                    content = item.summary if len(item.summary) > 0 else item.content

                    reasoning = "<think>\n"
                    for block in content:
                        reasoning += block.text
                    reasoning = reasoning.strip()
                    reasoning += "\n</think>"
                    print(reasoning)
                elif item.type == "function_call":
                    tool_name = item.name
                    args = json.loads(item.arguments)

                    tool_call_trace = f"<tool>\nname= {tool_name}, args={args}\n</tool>"
                    print(tool_call_trace)

                    result = call_tool(tool_name, args)

                    self._context_manager.extend(
                        [
                            {
                                "type": "function_call_output",
                                "call_id": item.call_id,
                                "output": json.dumps(result),
                            }
                        ]
                    )

                    result = self._intelligence.send_message(
                        self._context_manager.get_context()
                    )
                else:
                    raise ValueError(f"Unsupported response type: {item.type}")

            if not is_tool_call:
                break

        return response_text
