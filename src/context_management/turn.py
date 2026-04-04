from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class Turn(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage | None = None
