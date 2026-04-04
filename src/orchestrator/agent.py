from context_management.context_manager import ContextManager
from intelligence_layer.intelligence import Intelligence


class Agent:
    def __init__(self):
        self._context_manager = ContextManager()
        self._intelligence = Intelligence()

    def set_system_prompt(self, sys_prompt: str):
        self._context_manager.set_sys_prompt(sys_prompt)

    def step(self, message: str):
        context = self._context_manager.build_context(message)
        result = self._intelligence.send_message(context)

        self._context_manager.add_assistant_response(result)

        return result
