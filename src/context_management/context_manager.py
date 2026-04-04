from context_management.turn import Turn, ChatMessage


class ContextManager:
    def __init__(self):
        self._sys_prompt = ""
        self._turns: list[Turn] = []

    def set_sys_prompt(self, sys_prompt):
        self._sys_prompt = sys_prompt

    def build_context(self, prompt: str) -> list[dict]:
        turn = Turn(user_message=ChatMessage(role="user", content=prompt))

        self._turns.append(turn)

        result = [
            {"role": "system", "content": self._sys_prompt},
        ]

        for stored_turn in self._turns:
            result.extend(self._serialize_turn(stored_turn))

        # print(f"[DEBUG] - Context: {result}")

        return result

    def add_assistant_response(self, response_text: str):
        message = ChatMessage(role="assistant", content=response_text)
        latest_turn = self._turns[-1]
        latest_turn.assistant_message = message

    def _serialize_turn(self, turn: Turn) -> list[dict]:
        user_message = turn.user_message
        assistant_message = turn.assistant_message

        messages = [{"role": user_message.role, "content": user_message.content}]

        if assistant_message is not None:
            messages.append(
                {"role": assistant_message.role, "content": assistant_message.content}
            )

        return messages
