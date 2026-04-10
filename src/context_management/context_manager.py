from openai.types.responses.response_output_item import ResponseOutputItem


class ContextManager:
    def __init__(self):
        self._sys_prompt = "You are a helpful assistant."
        self._context: list = [{"role": "system", "content": self._sys_prompt}]

    def get_context(self):
        return self._context

    def set_sys_prompt(self, sys_prompt):
        self._sys_prompt = sys_prompt

        self._context[0] = {"role": "system", "content": self._sys_prompt}

    def build_context(self, prompt: str) -> list[dict]:
        self._context.append({"role": "user", "content": prompt})

        return self._context

    def add_assistant_response(self, response_text: str):
        self._context.append({"role": "asssitant", "content": response_text})

    def latest(self):
        return self._context[-1]

    def extend(self, context: list[ResponseOutputItem]):
        self._context.extend(context)
