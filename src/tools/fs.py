import json
import os

SANDBOX_ROOT = "/home/avgdev/sandbox"

WRITE_MODE_SET = {"r", "w", "x", "a", "t", "+"}
READ_MODE_SET = {"r", "w", "x", "a", "b", "t", "+"}


def _is_parent_traversal(path: str):
    if "../" in path or "/.." in path:
        return True
    return False


def _sanitize_mode(mode: str, is_write: bool = False):
    result = ""

    MODE_SET = WRITE_MODE_SET if is_write else READ_MODE_SET

    for c in mode:
        if c in MODE_SET:
            result += c

    return result


def _make_real_path(filepath: str) -> str:
    real_path = SANDBOX_ROOT

    if not filepath.startswith(SANDBOX_ROOT):
        real_path = f"{SANDBOX_ROOT}/{filepath}"
    else:
        real_path = filepath

    return real_path


def fs_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """Writes a file with contents given a filepath within the sandbox directory.

    File path is something like: {sandbox_root}/{filepath}. If no sandbox root is prepended, it will be done so automatically. To find the sandbox directory, run the "get_root_dir" function.

    Default mode is w (write).

    Returns
        - Information about the number of bytes written.
    """
    if _is_parent_traversal(filepath):
        return json.dumps(
            {
                "status": "error",
                "result": "Parent traversals not allowed. Please provide absolute directory.",
            }
        )

    real_path = _make_real_path(filepath)

    bytes_written = 0
    try:
        with open(real_path, _sanitize_mode(mode, is_write=True)) as f:
            bytes_written = f.write(content)

        return json.dumps({"status": "ok", "result": {"bytes_written": bytes_written}})
    except IOError as e:
        return json.dumps(
            {"status": "error", "result": f"Could not write the file: {real_path}"}
        )


def fs_read_file(filepath: str, mode: str = "r") -> str:
    """Reads a file and gets contents as a string given the filepath within the sandbox root.

    File path is something like: {sandbox_root}/{filepath}. If no sandbox root is prepended, it will be done so automatically. To find the sandbox directory, run the "get_root_dir" function.

    Default mode is "r" (read).

    Returns:
        - Information including contents of the file at given filepath.
    """
    if _is_parent_traversal(filepath):
        return json.dumps(
            {
                "status": "error",
                "result": "Parent traversals not allowed. Please provide absolute directory.",
            }
        )
    real_path = _make_real_path(filepath)

    content = ""
    try:
        with open(real_path, _sanitize_mode(mode)) as f:
            content = f.read()

        return json.dumps({"status": "ok", "result": {"contet": content}})
    except IOError as e:
        return json.dumps(
            {"status": "error", "result": f"Could not read the file: {real_path}"}
        )


def fs_make_directory(filepath: str, create_parent_if_not_exists: bool = False) -> str:
    """Creates a directory at the filepath within the sandbox root.

    File path is something like: {sandbox_root}/{filepath}. If no sandbox root is prepended, it will be done so automatically. To find the sandbox directory, run the "get_root_dir" function.

    Returns:
        - Information and filepath of the directory created.
    """
    if _is_parent_traversal(filepath):
        return json.dumps(
            {
                "status": "error",
                "result": "Parent traversals not allowed. Please provide absolute directory.",
            }
        )
    real_path = _make_real_path(filepath)

    try:
        if create_parent_if_not_exists:
            os.makedirs(real_path, exist_ok=True)
        else:
            os.mkdir(real_path)

        return json.dumps(
            {"status": "ok", "result": f"Created directory at: {real_path}"}
        )
    except Exception as e:
        return json.dumps(
            {"status": "error", "result": f"Could not make directory: {real_path}"}
        )


def fs_list_directory(filepath: str) -> str:
    """Gets the filenames at the current directory specified by the filepath within the sandbox root.

    File path is something like: {sandbox_root}/{filepath}. If no sandbox root is prepended, it will be done so automatically. To find the sandbox directory, run the "get_root_dir" function.

    Returns:
        - Information about the list of filenames at the current directory.
    """
    if _is_parent_traversal(filepath):
        return json.dumps(
            {
                "status": "error",
                "result": "Parent traversals not allowed. Please provide absolute directory.",
            }
        )
    real_path = _make_real_path(filepath)

    if not os.path.exists(real_path):
        return json.dumps(
            {"status": "error", "result": f"Path does not exist: {real_path}"}
        )

    dirs = os.listdir(real_path)
    dirs = list(filter(lambda x: x not in ["..", "."], dirs))

    return json.dumps({"status": "ok", "result": dirs})


def fs_file_exists(filepath: str) -> str:
    """Checks if the file exists specified by the filepath within the sandbox root.

    File path is something like: {sandbox_root}/{filepath}. If no sandbox root is prepended, it will be done so automatically. To find the sandbox directory, run the "get_root_dir" function.

    Returns:
        - Information if the file exists.
    """
    if _is_parent_traversal(filepath):
        return json.dumps(
            {
                "status": "error",
                "result": "Parent traversals not allowed. Please provide absolute directory.",
            }
        )
    real_path = _make_real_path(filepath)

    result = os.path.exists(real_path)

    return json.dumps({"status": "ok", "result": result})


def fs_get_root_dir() -> str:
    """Gets the filepath to the sandbox root.

    Returns:
        - The path of the sandbox root.
    """
    return json.dumps({"status": "ok", "result": SANDBOX_ROOT})
