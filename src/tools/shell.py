import subprocess
import os
from typing import Any

BLOCKED_COMMANDS: set[str] = {"sudo"}


def shell_exec_sync(
    program: str, arguments: list[str], env: dict[str, str] = {}, timeout: int = 120
) -> dict[str, Any]:
    """
    Spawns a subprocess given the program and list of argumentss.

    This runs synchronously, so program are blocked in the meantime!

    Environment variables can be specified, otherwise a default environment is created by inheriting from the current OS.

    Default timeout is 120 seconds for the command to return some result.
    """

    if not program:
        return "ERROR: No program name was given."

    if "sudo" in program:
        return {"status": "failure", "message": "sudo commands are not allowed."}

    for blocked in BLOCKED_COMMANDS:
        if blocked in program:
            return {"status": "failure", "message": "Blocked command."}

    try:
        result = subprocess.run(
            [program, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, **env},
        )
    except FileNotFoundError:
        return {
            "status": "failure",
            "message": "No such file or directory. Program not found in PATH. Suggestion: Call this tool with a valid program with arguments as an array.",
        }

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }
