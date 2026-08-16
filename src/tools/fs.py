import os

from tools.base_tool import BaseTool
from tools.helpers import ToolError, err, guarded_path, ok

WRITE_MODE_SET = {"r", "w", "x", "a", "t", "+"}
READ_MODE_SET = WRITE_MODE_SET | {"b"}


def _sanitize_mode(mode: str, is_write: bool = False) -> str:
    """Keep only the mode characters Python's open() actually understands."""
    mode_set = WRITE_MODE_SET if is_write else READ_MODE_SET
    return "".join(c for c in mode if c in mode_set)


class WriteFileTool(BaseTool):
    name = "write_file"
    description = (
        "Writes a file with contents given a filepath. Can only write within the "
        "workspace directory."
    )
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": (
                    "filepath. parent relative paths will be resolved automatically. "
                    "path must include the workspace directory."
                ),
            },
            "content": {
                "type": "string",
                "description": "contents to write to the file",
            },
            "mode": {
                "type": "string",
                "description": "file operation mode. default: 'w'.",
            },
        },
        "required": ["filepath", "content"],
    }

    def invoke(self, **kwargs) -> dict:
        filepath = kwargs.get("filepath", "")
        content = kwargs.get("content", "")
        mode = kwargs.get("mode", "w")

        try:
            real_path = guarded_path(filepath, require_workspace=True)
        except ToolError as e:
            return err(str(e))

        try:
            with open(real_path, _sanitize_mode(mode, is_write=True)) as f:
                bytes_written = f.write(content)
        except IOError:
            return err(f"Could not write the file: {real_path}")

        return ok({"bytes_written": bytes_written})


class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Reads a file and gets contents as a string given the filepath."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "filepath. parent relative paths will be resolved automatically.",
            },
            "mode": {
                "type": "string",
                "description": "file operation mode. default: 'r'.",
            },
        },
        "required": ["filepath"],
    }

    def invoke(self, **kwargs) -> dict:
        filepath = kwargs.get("filepath", "")
        mode = kwargs.get("mode", "r")

        try:
            real_path = guarded_path(filepath, require_workspace=False)
        except ToolError as e:
            return err(str(e))

        try:
            with open(real_path, _sanitize_mode(mode)) as f:
                content = f.read()
        except IOError:
            return err(f"Could not read the file: {real_path}")
        except UnicodeDecodeError:
            return err(
                f"Could not read the file: {real_path}. "
                "Only text-based file reading is supported now."
            )

        return ok({"content": content})


class MakeDirectoryTool(BaseTool):
    name = "make_directory"
    description = (
        "Creates a directory at the filepath. Can only create directories within "
        "the workspace directory."
    )
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": (
                    "filepath. parent relative paths will be resolved automatically. "
                    "path must include the workspace directory."
                ),
            },
            "create_parent_if_not_exists": {
                "type": "boolean",
                "description": "Create all parent directories if true. Default false.",
            },
        },
        "required": ["filepath"],
    }

    def invoke(self, **kwargs) -> dict:
        filepath = kwargs.get("filepath", "")
        create_parent_if_not_exists = kwargs.get("create_parent_if_not_exists", False)

        try:
            real_path = guarded_path(filepath, require_workspace=True)
        except ToolError as e:
            return err(str(e))

        try:
            if create_parent_if_not_exists:
                os.makedirs(real_path, exist_ok=True)
            else:
                os.mkdir(real_path)
        except Exception:
            return err(f"Could not make directory: {real_path}")

        return ok(f"Created directory at: {real_path}")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "Gets the filenames at the current directory specified by the filepath."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "filepath. parent relative paths will be resolved automatically.",
            }
        },
        "required": ["filepath"],
    }

    def invoke(self, **kwargs) -> dict:
        filepath = kwargs.get("filepath", "")

        try:
            real_path = guarded_path(filepath, require_workspace=False)
        except ToolError as e:
            return err(str(e))

        if not os.path.exists(real_path):
            return err(f"Path does not exist: {real_path}")

        entries = [name for name in os.listdir(real_path) if name not in ("..", ".")]

        return ok(entries)


class FileExistsTool(BaseTool):
    name = "file_exists"
    description = "Checks if the file exists specified by the filepath."
    parameters = {
        "type": "object",
        "properties": {
            "filepath": {
                "type": "string",
                "description": "filepath. parent relative paths will be resolved automatically.",
            }
        },
        "required": ["filepath"],
    }

    def invoke(self, **kwargs) -> dict:
        filepath = kwargs.get("filepath", "")

        try:
            real_path = guarded_path(filepath, require_workspace=False)
        except ToolError as e:
            return err(str(e))

        return ok(os.path.exists(real_path))
