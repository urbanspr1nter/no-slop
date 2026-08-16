from pathlib import Path

from tools.base_tool import BaseTool
from tools.helpers import err, guarded_path, ok


class GlobTool(BaseTool):
    # glob only reads paths, so it is not confined to the workspace — but the
    # blocked-path check and real error reporting still apply.
    name = "glob"
    description = "Perform glob path search at the start path. Optionally recurse."
    parameters = {
        "type": "object",
        "properties": {
            "start_path": {
                "type": "string",
                "description": (
                    "Start path which will resolve to the absolute path to begin "
                    "glob search"
                ),
            },
            "glob_path": {"type": "string", "description": "glob path"},
            "recurse": {"type": "boolean", "description": "Recurse search"},
        },
        "required": ["start_path", "glob_path"],
    }

    def invoke(self, **kwargs) -> dict:
        start_path = kwargs.get("start_path", "")
        glob_path = kwargs.get("glob_path", "")
        recurse = kwargs.get("recurse", False)

        try:
            start = guarded_path(start_path, require_workspace=False)
        except Exception as e:
            return err(f"Can't perform glob search {glob_path} at path {start_path}: {e}")

        try:
            path = Path(start)
            if recurse:
                matches = [str(f) for f in path.rglob(glob_path)]
            else:
                matches = [str(f) for f in path.glob(glob_path)]
        except Exception as e:
            return err(f"Can't perform glob search {glob_path} at path {start_path}: {e}")

        return ok(matches)
