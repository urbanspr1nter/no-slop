import tools.ns_math as ns_math
import tools.fs as fs
import tools.shell as shell
import tools.file_edit_and_show_diff as edit


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
    elif tool_name == "write_file":
        filepath = args["filepath"]
        content = args["content"]
        mode = args.get("mode", "w")

        result = fs.fs_write_file(filepath, content, mode)
    elif tool_name == "read_file":
        filepath = args["filepath"]
        mode = args.get("mode", "r")

        result = fs.fs_read_file(filepath, mode)
    elif tool_name == "make_directory":
        filepath = args["filepath"]
        create_parent_if_not_exists = args.get("create_parent_if_not_exists", False)

        result = fs.fs_make_directory(filepath, create_parent_if_not_exists)
    elif tool_name == "list_directory":
        filepath = args["filepath"]

        result = fs.fs_list_directory(filepath)
    elif tool_name == "file_exists":
        filepath = args["filepath"]

        result = fs.fs_file_exists(filepath)
    elif tool_name == "shell_exec_sync":
        result = shell.shell_exec_sync(
            program=args.get("program", ""),
            arguments=args.get("arguments", []),
            env=args.get("env", {}),
            timeout=args.get("timeout", 120),
        )
    elif tool_name == "file_edit_and_show_diff":
        result = edit.file_edit_and_show_diff(
            old_str=args.get("old_str", ""),
            new_str=args.get("new_str", ""),
            filepath=args.get("filepath", ""),
        )
    else:
        result = {"status": "failure"}

    return result
