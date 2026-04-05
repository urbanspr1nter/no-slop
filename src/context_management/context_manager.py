from openai.types.responses.response_output_item import ResponseOutputItem

from tools.registry import MATH_TOOLS


class ContextManager:
    def __init__(self):
        self._sys_prompt = "You are a helpful assistant."
        self._turns: list = [{"role": "system", "content": self._sys_prompt}]
        self._tools: list = MATH_TOOLS

    def get_context(self):
        return self._turns

    def set_sys_prompt(self, sys_prompt):
        self._sys_prompt = sys_prompt

        # Update the system prompt
        self._turns[0] = {"role": "system", "content": self._sys_prompt}

    def build_context(self, prompt: str) -> list[dict]:
        self._turns.append({"role": "user", "content": prompt})

        return self._turns

    def add_assistant_response(self, response_text: str):
        self._turns.append({"role": "assistant", "content": response_text})

    def latest(self):
        return self._turns[-1]

    def extend(self, context: list[ResponseOutputItem]):
        self._turns.extend(context)
