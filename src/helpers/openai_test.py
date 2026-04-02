import openai

MODEL = "gemma-4-e4b-it"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send_message(prompt: str) -> str:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    response = client.responses.create(model=MODEL, input=prompt)

    return response.output_text


if __name__ == "__main__":
    result = send_message("Hi there, tell me a joke.")

    print(result)
