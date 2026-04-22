from intelligence_layer.llm import send
from config.loader import Config
from intelligence_layer.llm_provider import LlmProvider


class Intelligence:
    def __init__(self, config: Config):
        self._provider = LlmProvider(config)

    def send_message(self, context: list):
        return send(self._provider, context)
