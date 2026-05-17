from pydantic import BaseModel


class Config(BaseModel):
    base_endpoint: str = "http://localhost:8000/v1"
    api_key: str = "none"
    model_id: str = "gemma-4-E4B-it"


def load_config():
    return Config()
