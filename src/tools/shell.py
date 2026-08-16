import json
import os
import subprocess

from config.loader import load_config
from tools.base_tool import BaseTool
from tools.helpers import err, ok
from tools.truncate_with_label import truncate_with_label

BLOCKED_COMMANDS: set[str] = {"sudo"}


def _parse_json_field(value, field_name: str, expected: str):
    """Accept a JSON-encoded string for a field, otherwise pass it through."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            raise ValueError(f"{field_name} must be a valid {expected}.")
    return value


class ShellExecSyncTool(BaseTool):
    name = "shell_exec_sync"
    description = (
        'Run a shell command synchronously. Parameters are "program" (string) and '
        '"arguments" (array). Example: program="ls" arguments=["-la", "/etc/"]'
    )
    parameters = {
        "type": "object",
        "properties": {
            "program": {
                "type": "string",
                "description": "Program or builtin to run.",
            },
            "arguments": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of arguments including the switches and options. Pass as "
                    "literally array of strings."
                ),
            },
            "env": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "description": (
                    "Environment variables to set (key-value pairs). OS environment "
                    "will be extended with this."
                ),
            },
            "timeout": {
                "type": "number",
                "description": (
                    "Maximum number of seconds to execute the shell command. "
                    "Default=120 seconds if not provided."
                ),
            },
        },
        "required": ["program"],
    }

    def _write_log(self, **kwargs) -> str | None:
        tool_call_id = kwargs.get("tool_call_id", "")
        if not tool_call_id:
            return None

        config = load_config()
        abs_path = f"{config.temp_path}/{tool_call_id}.out"
        with open(abs_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "returncode": kwargs.get("returncode", ""),
                        "stdout": kwargs.get("stdout", ""),
                        "stderr": kwargs.get("stderr", ""),
                    },
                    indent=2,
                )
            )

        return abs_path

    def _truncate(self, call_id: str, **kwargs) -> dict:
        stdout = kwargs.get("stdout", "")
        stderr = kwargs.get("stderr", "")

        if not call_id:
            return {"truncated": None, "full": {"stdout": stdout, "stderr": stderr}}

        config = load_config()
        return {
            "truncated": {
                "stdout": truncate_with_label(
                    stdout, max_length=config.max_tool_call_output_length
                ),
                "stderr": truncate_with_label(
                    stderr, max_length=config.max_tool_call_output_length
                ),
            },
            "full": {"stdout": stdout, "stderr": stderr},
        }

    def invoke(self, **kwargs) -> dict:
        """Run a program synchronously via bash.

        ``arguments`` and ``env`` may arrive as JSON-encoded strings (some models
        serialize them); both shapes are accepted and normalized here.
        """
        program = kwargs.get("program", "")
        arguments = kwargs.get("arguments", [])
        env = kwargs.get("env", {})
        tool_call_id = kwargs.get("tool_call_id", "")

        try:
            timeout = int(kwargs.get("timeout", load_config().shell_timeout))
        except (TypeError, ValueError):
            return err("Provide a valid integer for the timeout.")

        if not program:
            return err("Please provide a valid program.")

        if "sudo" in program or "sudo" in arguments:
            return err("sudo commands are not allowed.")

        if program in BLOCKED_COMMANDS:
            return err("Blocked command.")

        try:
            arguments = _parse_json_field(arguments, "arguments", "array")
            env = _parse_json_field(env, "env", "object")
        except ValueError as e:
            return err(str(e))

        try:
            result = subprocess.run(
                ["/bin/bash", "-c", f'{program} "$@"', "--", *arguments],
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ, **env},
            )
        except FileNotFoundError:
            return err(
                "No such file or directory. Program not found in PATH. Suggestion: "
                "Call this tool with a valid program with arguments as an array."
            )
        except subprocess.TimeoutExpired:
            return err(
                f"Shell command timeout expired. Specified timeout was: {timeout} "
                f"seconds. Default is: {load_config().shell_timeout} seconds"
            )

        truncate_result = self._truncate(
            call_id=tool_call_id, stdout=result.stdout, stderr=result.stderr
        )
        truncated = truncate_result["truncated"]
        full = truncate_result["full"]

        log_path = self._write_log(
            returncode=result.returncode,
            stdout=full["stdout"],
            stderr=full["stderr"],
            tool_call_id=tool_call_id,
        )

        return ok(
            {
                **(truncated if truncated is not None else full),
                "returncode": result.returncode,
                "full_output_log": log_path,
            }
        )
