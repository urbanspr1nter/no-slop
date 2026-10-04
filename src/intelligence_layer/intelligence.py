from intelligence_layer.llm import stream
from config.loader import Config
from intelligence_layer.llm_provider import LlmProvider


class Intelligence:
    def __init__(self, config: Config):
        self._provider = LlmProvider(config)

    async def send_message(self, context: list):
        return await stream(self._provider, context)
