import difflib

from tools.base_tool import BaseTool
from tools.helpers import ToolError, err, guarded_path, ok


class FileEditAndShowDiffTool(BaseTool):
    name = "file_edit_and_show_diff"
    description = (
        "Edits a file on disk given the string to replace with the new string. "
        "Returns a diff of edits after the process is done."
    )
    parameters = {
        "type": "object",
        "properties": {
            "old_str": {
                "type": "string",
                "description": "String to search for in the file to be replaced for edit.",
            },
            "new_str": {
                "type": "string",
                "description": "String to replace the old_str.",
            },
            "filepath": {
                "type": "string",
                "description": "Filepath of the file to edit.",
            },
        },
        "required": ["old_str", "new_str", "filepath"],
    }

    def invoke(self, **kwargs) -> dict:
        old_str = kwargs.get("old_str", "")
        new_str = kwargs.get("new_str", "")
        filepath = kwargs.get("filepath", "")

        # This tool writes to disk, so it is held to the same path policy as
        # write_file: blocked paths and the workspace boundary both apply.
        try:
            real_path = guarded_path(filepath, require_workspace=True)
        except ToolError as e:
            return err(str(e))

        try:
            with open(real_path, "r") as f:
                contents = f.read()
        except (FileNotFoundError, IOError):
            return err(
                f"Unknown error while attempting to read contents of file at: {real_path}. "
                "Could be not found or a generic IO error."
            )

        occurrences = contents.count(old_str)
        if occurrences == 0:
            return err(f"Couldn't find: {old_str} to replace.")
        if occurrences > 1:
            return err(f"More than 1 occurrence of string: {old_str}.")

        new_contents = contents.replace(old_str, new_str)

        diff = difflib.unified_diff(
            contents.splitlines(keepends=True),
            new_contents.splitlines(keepends=True),
            fromfile=real_path,
            tofile=real_path,
        )

        try:
            with open(real_path, "w") as f:
                f.write(new_contents)
        except (FileNotFoundError, IOError):
            return err(
                f"Unknown error while attempting to write contents to file at: {real_path}. "
                "Could be that it does not exist or is a generic IO error."
            )

        return ok(
            {
                "message": "File edited successfully. Diff is provided for reference.",
                "diff": "".join(diff),
            }
        )
