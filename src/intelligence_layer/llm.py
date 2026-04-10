import openai
from openai.types.responses.response_output_item import ResponseOutputItem
from tools.registry import TOOL_SET

MODEL = "qwen3.5-4b"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send(context: list) -> list[ResponseOutputItem]:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    response = client.responses.create(model=MODEL, input=context, tools=TOOL_SET)

    if response.status == "failed":
        raise ValueError("Cannot complete the request.")

    return response.output
