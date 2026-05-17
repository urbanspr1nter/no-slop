import difflib
import os


def file_edit_and_show_diff(old_str: str, new_str: str, filepath: str):
    """
    Edits the file where `old_str` occurs and replaces with `new_str`.

    The resulting diff will be returned after the file has been edited.
    """

    if not os.path.exists(filepath):
        return {"status": "failure", "message": f"File: {filepath} does not exist."}

    contents = ""

    try:
        with open(filepath, "r") as f:
            contents = f.read()
    except (FileNotFoundError, IOError):
        return {
            "status": "failure",
            "message": f"Unknown error while attempting to read contents of file at: {filepath}. Could be not found or an generic IO Error.",
        }

    if contents.count(old_str) == 0:
        return {"status": "failure", "message": f"Couldn't find: {old_str} to replace."}

    if contents.count(old_str) > 1:
        return {
            "status": "failure",
            "message": f"More than 1 occurrence of string: {old_str}.",
        }

    new_contents = contents.replace(old_str, new_str)

    diff = difflib.unified_diff(
        contents.splitlines(keepends=True),
        new_contents.splitlines(keepends=True),
        fromfile=filepath,
        tofile=filepath,
    )

    try:
        with open(filepath, "w") as f:
            f.write(new_contents)
    except (FileNotFoundError, IOError):
        return {
            "status": "failure",
            "message": f"Unknown error while attempting to write contents to file at: {filepath}. Could be that it does not exist or is a generic IO error.",
        }

    return {
        "status": "success",
        "message": "File edited successfully. Diff is provided for reference.",
        "diff": "".join(diff),
    }
