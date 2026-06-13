import tools.ns_math as ns_math
import tools.fs as fs
from tools.shell import ShellExecSyncTool
import tools.glob_tool as glob_tool
import tools.file_edit_and_show_diff as edit
import tools.web_search_and_scrape as web
import json

from config.loader import load_config

TOOL_INSTANCES = {"shell_exec_sync": ShellExecSyncTool()}


def call_tool(tool_name: str, tool_call_id: str, args: dict):
    config = load_config()
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
        filepath = args.get("filepath", "")
        content = args.get("content", "")
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
        arguments = args.get("arguments", [])
        if type(arguments) is str:
            try:
                arguments = json.loads(arguments)
            except:
                return {
                    "status": "failure",
                    "reason": "arguments must be a valid array",
                }

        env = args.get("env", {})
        if type(env) is str:
            try:
                env = json.loads(env)
            except:
                return {
                    "status": "failure",
                    "reason": "provide a valid dictionary of environment variable key-value pairs",
                }

        shell_exec_sync_tool: ShellExecSyncTool = TOOL_INSTANCES["shell_exec_sync"]

        result = shell_exec_sync_tool.invoke(
            program=args.get("program", ""),
            arguments=arguments,
            env=env,
            timeout=args.get("timeout", config.shell_timeout),
            tool_call_id=tool_call_id,
        )
    elif tool_name == "file_edit_and_show_diff":
        result = edit.file_edit_and_show_diff(
            old_str=args.get("old_str", ""),
            new_str=args.get("new_str", ""),
            filepath=args.get("filepath", ""),
        )
    elif tool_name == "glob":
        result = glob_tool.glob(
            start_path=args.get("start_path", ""),
            glob_path=args.get("glob_path", ""),
            recurse=args.get("recurse", False),
        )
    elif tool_name == "web_search":
        result = web.web_search(
            query=args.get("query", ""), limit=args.get("limit", 10)
        )
    elif tool_name == "web_page_scrape":
        result = web.web_page_scrape(url=args.get("url", ""))
    else:
        result = {"status": "failure"}

    return result
