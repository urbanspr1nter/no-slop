import tools.ns_math as ns_math


def call_tool(tool_name: str, args: dict):
    result = {"status": "failure"}
    if tool_name == "sqrt":
        x = args["x"]
        result = {"status": "ok", "result": ns_math.sqrt(x)}
    elif tool_name == "sum":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.sum(x, y)}
    elif tool_name == "sub":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.sub(x, y)}
    elif tool_name == "mult":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.mult(x, y)}
    elif tool_name == "div":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.div(x, y)}
    elif tool_name == "pow":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.pow(x, y)}
    elif tool_name == "mod":
        x = args["x"]
        y = args["y"]
        result = {"status": "ok", "result": ns_math.mod(x, y)}
    else:
        result = {"status": "failure"}

    return result
