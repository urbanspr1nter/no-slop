import openai
import json
from tools.call_tool import call_tool
from tools.registry import MATH_TOOLS

MODEL = "copaw-flash-4B"
BASE_API_ENDPOINT = "http://127.0.0.1:8000/v1"
API_KEY = "none"


def send_message(prompt: str) -> str:
    client = openai.Client(base_url=BASE_API_ENDPOINT, api_key=API_KEY)

    context = [
        {
            "role": "system",
            "content": "You are a grandmaster in mathematics. If necessary, perform tool calls step by step to solve the problem.",
        },
        {"role": "user", "content": prompt},
    ]

    response = client.responses.create(
        model=MODEL, tools=MATH_TOOLS, input=context, reasoning={"summary": "auto"}
    )

    response_text = ""

    while True:
        context.extend(response.output)

        print()
        print(response.output)
        print()

        is_tool_call = False
        for item in response.output:
            if item.type == "function_call":
                is_tool_call = True
            else:
                is_tool_call = False

            if item.type == "message":
                response_text = response.output_text
            elif item.type == "reasoning":
                content = item.summary if len(item.summary) > 0 else item.content
                reasoning = "<think>\n"
                for block in content:
                    reasoning += block.text
                reasoning = reasoning.strip()
                reasoning += "\n</think>"
                print(reasoning)
            elif item.type == "function_call":
                tool_name = item.name
                args = json.loads(item.arguments)

                tool_call_trace = (
                    "<tool>\n" f"Calling tool: {tool_name}, args: {args}" "\n</tool>"
                )
                print(tool_call_trace)

                result = call_tool(tool_name, args)

                context.append(
                    {
                        "type": "function_call_output",
                        "call_id": item.call_id,
                        "output": json.dumps(result),
                    }
                )

                # send back the result of the tool call back to LLM
                response = client.responses.create(
                    model=MODEL,
                    tools=MATH_TOOLS,
                    input=context,
                    reasoning={"summary": "auto"},
                )
            else:
                raise ValueError("Unsupported response type.")

        if not is_tool_call:
            break

    return response_text


if __name__ == "__main__":

    result = send_message(
        "square root of 121, then cube-root that and add 76 to it and finally divide by 13."
    )

    print(result)
