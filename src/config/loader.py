from pydantic import BaseModel


class Config(BaseModel):
    base_endpoint: str = "http://192.168.1.30:8000/v1"
    api_key: str = ""
    model_id: str = "qwen3.6-35b-a3b"


def load_config():
    return Config()
