"""Shared helpers for tools: result envelopes and path safety.

Every tool returns a uniform envelope with a ``status`` key:

- ``{"status": "ok", "result": <payload>, ...}``   see :func:`ok`
- ``{"status": "error", "result": ..., "message": ...}``   see :func:`err`

Path safety is centralized here so that all filesystem-touching tools
(write, read, edit, glob, mkdir, ...) enforce the same policy:

- A small set of blocked paths (e.g. dotfiles that should never be touched).
- Write operations are confined to the configured workspace directory.
"""

import os
from pathlib import Path

from config.loader import load_config
from utils.path_utils import make_real_path

HOME_DIRECTORY = str(Path.home())

# Paths that no tool — read or write — may touch.
BLOCKED_PATHS: frozenset[str] = frozenset(
    {
        str(Path(f"{HOME_DIRECTORY}/.bashrc").expanduser().resolve()),
        str(Path(f"{HOME_DIRECTORY}/.bash_profile").expanduser().resolve()),
    }
)


class ToolError(Exception):
    """Raised by a tool to signal a recoverable, model-visible failure."""


def ok(result=None, **extra) -> dict:
    """Build a success envelope: ``{"status": "ok", "result": ..., **extra}``."""
    return {"status": "ok", "result": result, **extra}


def err(message: str, result=None) -> dict:
    """Build an error envelope: ``{"status": "error", "result": ..., "message": ...}``."""
    return {"status": "error", "result": result, "message": message}


def is_blocked_path(filepath: str) -> bool:
    """True if the resolved path is in BLOCKED_PATHS."""
    return make_real_path(filepath) in BLOCKED_PATHS


def ensure_in_workspace(real_path: str) -> str:
    """Raise ToolError unless ``real_path`` is the workspace or inside it.

    ``real_path`` must already be absolute (see make_real_path).
    """
    config = load_config()
    workspace = make_real_path(config.workspace)

    if real_path != workspace and not real_path.startswith(workspace.rstrip("/") + "/"):
        raise ToolError(
            f"Path is outside the workspace directory. "
            f"Current workspace directory: {config.workspace}."
        )

    return real_path


def guarded_path(filepath: str, *, require_workspace: bool) -> str:
    """Resolve and safety-check a tool-supplied path.

    Applies the blocked-path check always; additionally enforces workspace
    containment when ``require_workspace`` is True (for write operations).

    Returns the absolute path or raises :class:`ToolError`.
    """
    real_path = make_real_path(filepath)

    if is_blocked_path(real_path):
        raise ToolError(f"{real_path} is not allowed.")

    if require_workspace:
        ensure_in_workspace(real_path)

    return real_path
