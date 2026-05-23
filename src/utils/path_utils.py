import os
from pathlib import Path


def make_real_path(p: str) -> str:
    working_p = p.replace("$HOME", os.getenv("HOME", "$HOME"))

    resolved = Path(working_p).expanduser().resolve()

    return str(resolved)
