# AGENTS.md

Guidance for AI coding agents working in this repository. Read this file fully before touching code. It is written for agents, not humans — the README covers intent and history; this file covers how to work here without breaking things.

## Project

`no-slop` is a TUI/CLI agentic-AI client written in Python. It talks to an LLM through the OpenAI Responses API (not chat completions): the agent streams the model's response, executes any tool calls the model makes in Python, and feeds results back into context until the model produces a final message.

- Entry point: `src/interface/streaming_client.py`; the `./no-slop` script wraps it (`-s` system prompt, `-w` workspace, `-p` headless prompt, `--session-resume <id>`).
- Core loop: `src/orchestrator/streaming_agent.py` — `StreamingAgent.step()`.
- Config: `~/.noslop/config.json` (user-level, lives outside the repo). `config.default.json` is the safe template — never commit real endpoints or keys.
- Runs on Linux, macOS, and Windows. Platform detection in `streaming_client.py` handles all three. The interactive TUI needs a POSIX `curses` terminal; on Windows, use headless mode (`-p`).

## Environment and commands

- `./install.sh` creates `.venv` and installs. On Debian/Ubuntu, `python3 -m venv` may lack `ensurepip`; if so, create with `--without-pip` and bootstrap pip via `get-pip.py` (or `sudo apt install python3-venv`).
- Every command runs through `.venv/bin/python` — never bare `python`.
- Install with `pip install -e .` only. All dependencies are declared in `pyproject.toml` (package name `mypackage`, src-layout, sources under `src/`), and the editable install is what makes the top-level imports resolve. Never use plain `pip install .`: it copies the sources into site-packages, and edits to `src/` then silently stop taking effect.
- **Keep `httpx` in `pyproject.toml` dependencies.** The web tools import it, and `openai` 3.x has its own forked `httpx2`, so it is not installed transitively — dropping it breaks every import.

To verify changes without an LLM server running:

- `.venv/bin/python -m compileall -q src` — syntax check.
- `.venv/bin/python -c "import orchestrator.streaming_agent, tools.registry"` — import smoke test.
- `.venv/bin/python tests/tui_test.py` — the only test suite (curses TUI logic + e2e screen assertions under a PTY with a fake agent). Run it before committing anything near the TUI or the agent event flow.
- `./no-slop -p "smoke"` should fail with `openai.APIConnectionError` (connection refused) and nothing earlier — any earlier failure is a startup regression.

## Architecture

```
interface.streaming_client    entry: curses TUI (interactive) / headless (-p)
  ├─ interface.curses_tui      curses UI: scrolling message pane + growing input box
  └─ orchestrator.streaming_agent   StreamingAgent.step() — stream → tool exec loop
       ├─ intelligence_layer        Responses API client (streaming only)
       ├─ interface.stream.processor   turns stream events into (token, state) steps
       ├─ context_management        in-memory context
       ├─ sessions                  JSON persistence in ~/.noslop/sessions/
       └─ tools                     the tool layer (see below)
```

- Imports are top-level against `src/` (e.g. `from orchestrator.streaming_agent import StreamingAgent`), resolved via the editable install.
- Rendering is pluggable: the curses TUI installs an event sink callable on `StreamingAgent.renderer`; headless and plain-terminal runs print to stdout instead. The event contract is documented in `src/interface/curses_tui.py`.

## Tools layer (read `documentation/04-Tools.md` first)

- Every tool is a `BaseTool` subclass in `src/tools/` with class attrs `name`, `description`, `parameters` and an `invoke(**kwargs)` method.
- Every tool returns a normalized envelope: `{"status": "ok", "result": ...}` or `{"status": "error", "result": ..., "message": ...}` (helpers `ok`/`err`). Exceptions never escape: `BaseTool.run()` catches them.
- `registry.py` derives the model-facing `TOOL_SET` from the tool classes — do not hand-edit schemas or `call_tool.py` dispatch.
- **Adding a tool = one class + one line in `registry.py`. Nothing else.**
- Path safety (`tools/helpers.py`): write operations are confined to the configured workspace, and a small blocked-path list (e.g. `~/.bashrc`) is off-limits for reads and writes alike. Use `guarded_path` instead of calling `open()` directly in filesystem tools.
- Result truncation/logging: `truncate_with_label.py` + per-call log files under the configured `temp_path`.

## Conventions

- Minimal, standard-library-first Python. No codegen, no scaffolding.
- Match the existing flat, duck-typed style; keep modules small and single-purpose.
- `documentation/` is the numbered series 01–05 and nothing else. Match its terse note style.
- **Write prose in natural flowing paragraphs.** Do not hard-wrap sentences with manual line breaks and do not use trailing-two-space line breaks. This project deliberately avoids "weird" line breaks in docs, messages, and summaries — write naturally and concisely.

## Gotchas

- The interactive UI is `interface/curses_tui.py`, stdlib `curses` only — **no TUI framework**. The owner explicitly wants no heavy libraries; do not reintroduce prompt_toolkit or textual (dead experiments were deleted long ago). See `documentation/05-TUI.md`.
- This is a TUI app, not a web service. Starting a new server does not update anything here; there is no HMR of any kind.
- The web tools (`web_search`, `web_page_scrape`) call an external search-and-scrape service configured via `search_and_scrape_service_url` in the config. That service is not part of this repo; without it the tools return an error envelope. `install.sh` installs Node.js (via volta) if missing — that is for the service, not for this Python package.
- Git: commit with the repo-local identity already configured. This is a public repo — scan diffs for secrets before committing anything credential-adjacent.

## Recently removed — do not look for these (October 2026 cleanup)

A cleanup pass removed things an older session might still assume exist. If a task seems to need one of them, it does not — ask the owner instead of rebuilding:

- `setup.py` and `requirements.txt` — replaced by `pyproject.toml` (src-layout, editable install).
- `docs-gen`, `create_tutorial_prompt.py`, and the whole documentation-generation workflow: prompt templates, the amber-manual style spec, `documentation/building-a-coding-agent/`, `documentation/html-tutorial-generator/`, and the doc-generation evals (L3, L4, L6).
- `src/interface/main.py` (dead pre-streaming entry point) and the non-streaming request path in `intelligence_layer`.
- Unused helpers: `ContextManager.add_assistant_response`/`extend`, the `noslop_*` file helpers.
- All remote branches except `main`. `main` is the only branch, and it is pushed.
