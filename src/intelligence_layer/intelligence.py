from intelligence_layer.llm import send


class Intelligence:
    def __init__(self):
        pass

    def send_message(self, context: list):
        return send(context)
