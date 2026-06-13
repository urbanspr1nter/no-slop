import subprocess
import os
import json
from tools.base_tool import BaseTool
from config.loader import load_config
from tools.truncate_with_label import truncate_with_label

BLOCKED_COMMANDS: set[str] = {"sudo"}


class ShellExecSyncTool(BaseTool):
    def _write_log(self, **kwargs):
        tool_call_id = kwargs.get("tool_call_id", "")
        if not tool_call_id:
            return None

        config = load_config()
        returncode = kwargs.get("returncode", "")
        stdout = kwargs.get("stdout", "")
        stderr = kwargs.get("stderr", "")

        abs_path = f"{config.temp_path}/{tool_call_id}.out"
        with open(abs_path, "w") as f:
            f.write(
                json.dumps(
                    {
                        "returncode": returncode,
                        "stdout": stdout,
                        "stderr": stderr,
                    },
                    indent=2,
                )
            )

        return abs_path

    def _truncate(self, call_id: str, **kwargs):
        if not call_id:
            return {"truncated": None, "full": {"stdout": stdout, "stderr": stderr}}

        config = load_config()
        stdout = kwargs.get("stdout", "")
        stderr = kwargs.get("stderr", "")

        truncated_stdout = truncate_with_label(
            stdout, max_length=config.max_tool_call_output_length
        )
        truncated_stderr = truncate_with_label(
            stderr, max_length=config.max_tool_call_output_length
        )

        return {
            "truncated": {
                "stdout": truncated_stdout,
                "stderr": truncated_stderr,
            },
            "full": {"stdout": stdout, "stderr": stderr},
        }

    def invoke(self, **kwargs):
        """Spawn a subprocess given the program and list of arguments.

        This runs synchronously, so the program is blocked in the meantime!!!

        Environment variables can be specified, otherwise a default environment is created by inheriting from the current OS.

        Default timeout is 120 seconds for the command to return some result.
        """

        program = kwargs.get("program", None)
        arguments = kwargs.get("arguments", {})
        env = kwargs.get("env", {})
        timeout = kwargs.get("timeout", 120)
        tool_call_id = kwargs.get("tool_call_id", "")

        if not program:
            return {"status": "failure", "message": "Please provide a valid program."}

        if "sudo" in program or "sudo" in arguments:
            return {"status": "failure", "message": "sudo commands are not allowed."}

        if program in BLOCKED_COMMANDS:
            return {"status": "failure", "message": "Blocked command."}

        try:
            result = subprocess.run(
                ["/bin/bash", "-c", f'{program} "$@"', "--", *arguments],
                capture_output=True,
                text=True,
                timeout=int(timeout),
                env={**os.environ, **env},
            )
        except FileNotFoundError:
            return {
                "status": "failure",
                "message": "No such file or directory. Program not found in PATH. Suggestion: Call this tool with a valid program with arguments as an array.",
            }

        truncate_result = self._truncate(
            call_id=tool_call_id, stdout=result.stdout, stderr=result.stderr
        )

        truncated = truncate_result["truncated"]
        full_result = truncate_result["full"]

        log_path = self._write_log(
            returncode=result.returncode,
            stdout=full_result["stdout"],
            stderr=full_result["stderr"],
            tool_call_id=tool_call_id,
        )

        return {
            **truncated,
            "returncode": result.returncode,
            "full_output_log": log_path,
        }
