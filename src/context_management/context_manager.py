class ContextManager:
    def __init__(self):
        self._sys_prompt = "You are a helpful assistant."
        self._context: list = [{"role": "system", "content": self._sys_prompt}]

    def get_context(self):
        return self._context

    def set_sys_prompt(self, sys_prompt):
        self._sys_prompt = sys_prompt

        self._context[0] = {"role": "system", "content": self._sys_prompt}

    def set_context(self, context: list):
        self._context = context

    def build_context(self, prompt: str) -> list[dict]:
        self._context.append(
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        )

        return self._context

    def append_context(self, item):
        self._context.append(item)

    def latest(self):
        return self._context[-1]
