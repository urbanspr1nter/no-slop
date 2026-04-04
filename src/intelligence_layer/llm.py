import openai

MODEL = "gemma-4-e4b-it"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send(context: list) -> str:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    response = client.responses.create(model=MODEL, input=context)

    if response.status == "failed":
        raise ValueError("Cannot complete the request.")

    return response.output_text
