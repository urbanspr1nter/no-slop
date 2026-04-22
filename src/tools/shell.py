from typing import Any
import subprocess
import os

BLOCKED_COMMANDS: set[str] = {"sudo"}


def shell_exec_sync(
    program: str, arguments: list[str], env: dict[str, str] = {}, timeout: int = 120
) -> dict[str, Any]:
    """Spawn a subprocess given the program and list of arguments.

    This runs synchronously, so the program is blocked in the meantime!!!

    Environment variables can be specified, otherwise a default environment is created by inheriting from the current OS.

    Default timeout is 120 seconds for the command to return some result.
    """

    if not program:
        return {"status": "failure", "message": "Please provide a valid program."}

    if "sudo" in program or "sudo" in arguments:
        return {"status": "failure", "message": "sudo commands are not allowed."}

    if program in BLOCKED_COMMANDS:
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
