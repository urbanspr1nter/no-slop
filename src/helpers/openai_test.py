import openai
import json
import tools.ns_math as ns_math
from tools.registry import MATH_TOOLS

MODEL = "qwen3.5-0.8b"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send_message(prompt: str) -> str:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    context = [{"role": "user", "content": prompt}]

    response = client.responses.create(model=MODEL, tools=MATH_TOOLS, input=context)

    while True:
        context.extend(response.output)

        print("The current LLM response:")
        print()
        print(response.output)
        print()

        for item in response.output:
            if item.type == "message":
                print(response.output_text)

                filtered_len = len(
                    list(filter(lambda x: x.type == "function_call", response.output))
                )
                if filtered_len == 0:
                    return response.output_text

            elif item.type == "function_call":
                args = json.loads(item.arguments)

                result = {"status": "failure"}

                if item.name == "sqrt":
                    x = args["x"]
                    result = {"status": "ok", "result": ns_math.sqrt(x)}
                elif item.name == "sum":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.sum(x, y)}
                elif item.name == "sub":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.sub(x, y)}
                elif item.name == "mult":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.mult(x, y)}
                elif item.name == "div":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.div(x, y)}
                elif item.name == "pow":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.pow(x, y)}
                elif item.name == "mod":
                    x = args["x"]
                    y = args["y"]
                    result = {"status": "ok", "result": ns_math.pow(x, y)}
                else:
                    result = {"status": "failure"}

                context.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                )

                # send back the result of the tool call back to LLM
                response = client.responses.create(
                    model=MODEL, tools=MATH_TOOLS, input=context
                )
            elif item.type == "reasoning":
                print("Reasoning")
            else:
                raise ValueError("Unsupported response type.")


if __name__ == "__main__":

    result = send_message(
        "square root of 121, then cube-root that and add 76 to it and finally divide by 13."
    )

    print(result)
