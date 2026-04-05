import openai
import json
import tools.ns_math as ns_math

MODEL = "qwen3.5-0.8b"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


TOOLS = [
    {
        "type": "function",
        "name": "sqrt",
        "description": "Computes the square root of a given number.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The number you want to square root.",
                }
            },
            "required": ["x"],
        },
    },
    {
        "type": "function",
        "name": "sum",
        "description": "Computes the sum of 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "sub",
        "description": "Computes the difference between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "mult",
        "description": "Computes the product between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "div",
        "description": "Computes the quotient between 2 numbers. Raises a ZeroDivisionError if attempting to divide by 0.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "pow",
        "description": "Computes x raised to y power.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
    {
        "type": "function",
        "name": "mod",
        "description": "Computes the modulo between 2 numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "The first operand.",
                },
                "y": {"type": "number", "description": "The second operand."},
            },
            "required": ["x", "y"],
        },
    },
]


def send_message(prompt: str) -> str:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    context = [{"role": "user", "content": prompt}]

    response = client.responses.create(model=MODEL, tools=TOOLS, input=context)

    while True:
        context.extend(response.output)

        print("The current LLM response:")
        print()
        print(response.output)
        print()

        for item in response.output:
            if item.type == "message":
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
                    model=MODEL, tools=TOOLS, input=context
                )
            else:
                raise ValueError("Unsupported response type.")


if __name__ == "__main__":

    result = send_message(
        "square root of 121, then cube-root that and add 76 to it and finally divide by 13."
    )

    print(result)
