from config.loader import Config


class LlmProvider:
    def __init__(self, config: Config):
        self.base_endpoint = config.base_endpoint
        self.api_key = config.api_key
        self.model_id = config.model_id
