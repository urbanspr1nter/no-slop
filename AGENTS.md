# AGENTS.md

Guidance for AI coding agents working in this repository. Read this before touching code. It is written for agents, not humans — the README covers intent and history; this file covers how to work here without breaking things.

## Project

`no-slop` is a TUI/CLI agentic-AI client written in Python. It talks to an LLM through the OpenAI Responses API (not chat completions): the agent streams the model's response, executes any tool calls the model makes in Python, and feeds results back into context until the model produces a final message.

- Entry point: `src/interface/streaming_client.py`; the `./no-slop` script wraps it (`-s` system prompt, `-w` workspace, `-p` headless prompt, `--session-resume <id>`).
- Core loop: `src/orchestrator/streaming_agent.py`.
- Config: `~/.noslop/config.json` (user-level; gitignored). `config.default.json` is the safe template — never commit real endpoints or keys.

## Environment

- `./install.sh` creates `.venv` and installs. On Debian/Ubuntu, `python3 -m venv` may lack `ensurepip`; if so, create with `--without-pip` and bootstrap pip via `get-pip.py` (or `sudo apt install python3-venv`).
- Every command runs through `.venv/bin/python` — never bare `python`.
- `pip install -r requirements.txt` then `pip install -e .` (package name is `mypackage`; sources live under `src/`).
- **Keep `httpx` in `setup.py` `install_requires`.** The web tools import it, and `openai` 3.x has its own forked `httpx2`, so it is not installed transitively — dropping it breaks every import.

## Architecture

```
interface.streaming_client  CLI prompt loop (prompt_toolkit)
  └─ orchestrator.streaming_agent   StreamingAgent.step() — stream → tool exec loop
       ├─ intelligence_layer        Responses API client (stream / non-stream)
       ├─ context_management        in-memory context
       ├─ sessions                  JSON persistence in ~/.noslop/sessions/
       └─ tools                     the tool layer (see below)
```

Imports are top-level against `src/` (e.g. `from orchestrator.streaming_agent import StreamingAgent`), resolved via the editable install.

## Tools layer (read `documentation/04-Tools.md`)

- Every tool is a `BaseTool` subclass in `src/tools/` with class attrs `name`, `description`, `parameters` and an `invoke(**kwargs)` method.
- Every tool returns a normalized envelope: `{"status": "ok", "result": ...}` or `{"status": "error", "result": ..., "message": ...}` (helpers `ok`/`err`). Exceptions never escape: `BaseTool.run()` catches them.
- `registry.py` derives the model-facing `TOOL_SET` from the tool classes — do not hand-edit schemas or `call_tool.py` dispatch.
- **Adding a tool** = one class + one line in `registry.py`. Nothing else.
- Path safety (`tools/helpers.py`): write tools are confined to the configured workspace and blocked paths (e.g. `~/.bashrc`); use `guarded_path` instead of calling `open()` directly in filesystem tools.
- Result truncation/logging: `truncate_with_label.py` + per-call log files.

## Gotchas

- The interactive `?` prompt uses prompt_toolkit multiline: **submit with Escape+Enter**, not Enter (Enter inserts a newline). A clean fix is a planned interface refactor; until then do not "fix" it piecemeal.
- Starting a new server does not update anything here — this is a TUI app, not a web service. There is no HMR of any kind.
- There is no real test suite: `src/helpers/*_test.py` are ad-hoc scripts. `src/helpers/smoke_test.py` is the closest thing to a fast sanity check.
- `documentation/` is a numbered series (01..04). Match its terse note style.
- Git: commit with the repo-local identity already configured. Public repo — run a quick scan for secrets before committing anything credential-adjacent.

## Conventions

- Minimal, standard-library-first Python. No codegen, no scaffolding.
- Match the existing flat, duck-typed style; keep modules small and single-purpose.
- **Write prose in natural flowing paragraphs.** Do not hard-wrap sentences with manual line breaks and do not use trailing-two-space line breaks. This project deliberately avoids "weird" line breaks in docs, messages, and summaries — write naturally and concisely.
