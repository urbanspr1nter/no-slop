import os
from pathlib import Path
from utils.path_utils import make_real_path
from config.loader import load_config

HOME_DIRECTORY = str(Path.home())

BLOCKED_PATHS: set[str] = {
    f"{HOME_DIRECTORY}/.bashrc",
    f"{HOME_DIRECTORY}/.bash_profile",
}

WRITE_MODE_SET = {"r", "w", "x", "a", "t", "+"}
READ_MODE_SET = {"r", "w", "x", "a", "b", "t", "+"}


def _is_blocked_path(filepath: str) -> bool:
    if filepath.strip() in BLOCKED_PATHS:
        return True
    else:
        return False


def _validate_is_workspace_path(filepath: str) -> bool:
    config = load_config()

    if not make_real_path(filepath).startswith(make_real_path(config.workspace)):
        return False

    return True


def _sanitize_mode(mode: str, is_write: bool = False):
    result = ""

    MODE_SET = WRITE_MODE_SET if is_write else READ_MODE_SET

    for c in mode:
        if c in MODE_SET:
            result += c

    return result


def fs_write_file(filepath: str, content: str, mode: str = "w") -> dict:
    """Writes a file with contents given a filepath within the configured workspace directory.

    Default mode is w (write).

    Returns
        - Information about the number of bytes written.
    """
    config = load_config()

    real_path = make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    if not _validate_is_workspace_path(real_path):
        return {
            "status": "failure",
            "message": f"You are only allowed to write files in the workspace directory. Current workspace directory: {config.workspace}.",
        }

    bytes_written = 0
    try:
        with open(real_path, _sanitize_mode(mode, is_write=True)) as f:
            bytes_written = f.write(content)

        return {"status": "ok", "result": {"bytes_written": bytes_written}}
    except IOError as e:
        return {"status": "error", "result": f"Could not write the file: {real_path}"}


def fs_read_file(filepath: str, mode: str = "r") -> dict:
    """Reads a file and gets contents as a string given the filepath.

    Default mode is "r" (read).

    Returns:
        - Information including contents of the file at given filepath.
    """
    real_path = make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    content = ""
    try:
        with open(real_path, _sanitize_mode(mode)) as f:
            content = f.read()

        return {"status": "ok", "result": {"content": content}}
    except IOError as e:
        return {"status": "error", "result": f"Could not read the file: {real_path}"}


def fs_make_directory(filepath: str, create_parent_if_not_exists: bool = False) -> dict:
    """Creates a directory at the filepath within the workspace directory.

    Returns:
        - Information and filepath of the directory created.
    """
    config = load_config()

    real_path = make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    if not _validate_is_workspace_path(real_path):
        return {
            "status": "failure",
            "message": f"You are only allowed to create directories within the workspace directory. Current workspace directory: {config.workspace}",
        }

    try:
        if create_parent_if_not_exists:
            os.makedirs(real_path, exist_ok=True)
        else:
            os.mkdir(real_path)

        return {"status": "ok", "result": f"Created directory at: {real_path}"}

    except Exception as e:
        return {"status": "error", "result": f"Could not make directory: {real_path}"}


def fs_list_directory(filepath: str) -> dict:
    """Gets the filenames within the given path.

    Returns:
        - Information about the list of filenames at the current directory.
    """
    real_path = make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    if not os.path.exists(real_path):
        return {"status": "error", "result": f"Path does not exist: {real_path}"}

    dirs = os.listdir(real_path)
    dirs = list(filter(lambda x: x not in ["..", "."], dirs))

    return {"status": "ok", "result": dirs}


def fs_file_exists(filepath: str) -> dict:
    """Checks if the file exists specified by the filepath.

    Returns:
        - Information if the file exists.
    """
    real_path = make_real_path(filepath)

    if _is_blocked_path(real_path):
        return {"status": "failure", "message": f"{real_path} is not allowed."}

    result = os.path.exists(real_path)

    return {"status": "ok", "result": result}
