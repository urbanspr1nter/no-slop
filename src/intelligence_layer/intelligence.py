from intelligence_layer.llm import send
from config.loader import Config
from intelligence_layer.llm_provider import LlmProvider


class Intelligence:
    def __init__(self, config: Config):
        self._provider = LlmProvider(config)

    async def send_message(self, context: list, should_stream: bool = False):
        if not should_stream:
            return send(self._provider, context)
