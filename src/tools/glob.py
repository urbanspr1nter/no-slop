from pathlib import Path


def glob(start_path: str, glob_path: str, recurse=False):
    """Glob search at the start path. Optionally recurse."""
    matches = []

    try:
        if not recurse:
            for file in Path(start_path).resolve().glob(glob_path):
                matches.append(str(file))
        else:
            for file in Path(start_path).resolve().rglob(glob_path):
                matches.append(str(file))

        return {"status": "success", "matches": matches}
    except:
        return {
            "status": "failure",
            "message": f"Can't perform glob search {glob_path} at path: {start_path}",
        }
