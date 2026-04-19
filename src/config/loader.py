from pydantic import BaseModel


class Config(BaseModel):
    base_endpoint: str = "http://127.0.0.1:8000/v1"
    api_key: str = ""
    model_id: str = "qwen3.5-4b"


def load_config():
    return Config()
