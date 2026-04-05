import openai
from openai.types.responses.response_output_item import ResponseOutputItem

from tools.registry import MATH_TOOLS

MODEL = "copaw-flash-4b"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send(context: list) -> list[ResponseOutputItem]:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    response = client.responses.create(
        model=MODEL, input=context, tools=MATH_TOOLS, reasoning={"summary": "auto"}
    )

    if response.status == "failed":
        raise ValueError("Cannot complete the request.")

    return response.output
