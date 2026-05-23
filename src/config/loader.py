from pydantic import BaseModel

_config = None


class Config(BaseModel):
    base_endpoint: str = "http://localhost:8000/v1"
    api_key: str = "none"
    model_id: str = "gemma-4-E2B-it"
    timeout: int = 7200
    workspace: str = "."


def load_config():
    global _config

    if _config is None:
        _config = Config()

    return _config
