import os
import json
import shutil
from pydantic import BaseModel
from utils.noslop_dir_utils import get_noslop_path

_config = None


class Config(BaseModel):
    base_endpoint: str = "http://localhost:8000/v1"
    api_key: str = "none"
    model_id: str = "qwen3.6-27b"
    timeout: int = 7200
    workspace: str = "."


def load_config():
    global _config

    noslop_path = get_noslop_path()
    noslop_config_path = f"{noslop_path}/config.json"

    if _config is None:
        _config = Config()

        _loaded_config = None
        if os.path.exists(noslop_config_path):
            with open(noslop_config_path, "r") as f:
                _loaded_config = json.loads(f.read())

        if _loaded_config is not None:
            provider = _loaded_config["provider"]
            provider_config = _loaded_config["providers"][provider]
            workspace_default = _loaded_config["workspace_default"]

            _config.base_endpoint = provider_config["base_endpoint"]
            _config.api_key = os.getenv(provider_config["api_key_env"], "sk-local")
            _config.model_id = provider_config["model"]
            _config.timeout = provider_config["timeout"]
            _config.workspace = workspace_default

            print(f"Loaded config defaults: {dict(_config)}")

    return _config
