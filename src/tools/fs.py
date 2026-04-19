import json
import os
from pathlib import Path

HOME_DIRECTORY = str(Path.home())

BLOCKED_PATHS = [
    f"{HOME_DIRECTORY}/.bashrc",
    f"{HOME_DIRECTORY}.bash_profile",
]

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


def _is_blocked_path(filepath: str) -> bool:
    if filepath.strip() in BLOCKED_PATHS:
        return True
    else:
        return False


def _make_real_path(filepath: str) -> str:
    real_path = str(Path(filepath).resolve())

    return real_path


def fs_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """Writes a file with contents given a filepath.

    Default mode is w (write).

    Returns
        - Information about the number of bytes written.
    """
    real_path = _make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

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
    """Reads a file and gets contents as a string given a filepath.

    Default mode is "r" (read).

    Returns:
        - Information including contents of the file at given filepath.
    """
    real_path = _make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

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
    """Creates a directory at the filepath.

    Returns:
        - Information and filepath of the directory created.
    """
    real_path = _make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

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
    """Gets the filenames at associated within the path.

    Returns:
        - Information about the list of filenames within the path.
    """
    real_path = _make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    if not os.path.exists(real_path):
        return json.dumps(
            {"status": "error", "result": f"Path does not exist: {real_path}"}
        )

    dirs = os.listdir(real_path)
    dirs = list(filter(lambda x: x not in ["..", "."], dirs))

    return json.dumps({"status": "ok", "result": dirs})


def fs_file_exists(filepath: str) -> str:
    """Checks if the file exists specified by the filepath.

    Returns:
        - Information if the file exists.
    """
    real_path = _make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    real_path = _make_real_path(filepath)

    result = os.path.exists(real_path)

    return json.dumps({"status": "ok", "result": result})
