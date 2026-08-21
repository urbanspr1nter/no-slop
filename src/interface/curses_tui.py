"""Curses TUI for no-slop.

A terminal interface with no dependencies beyond the standard library
``curses`` module.

Layout, top to bottom:

    +----------------------------------+
    | message pane (scrollable)        |
    |                                  |
    +----------------------------------+
    idle      enter send, up/down hist..  <- status/hint row
    +----------------------------------+
    | type a message                     |
    |                                     |
    +----------------------------------+

The input box sits at the bottom of the screen and grows from one line to
five (MAX_INPUT_LINES). Both the pane and the input wrap at the screen
width. The pane scrolls vertically (pgup/pgdn, mouse wheel) and follows new
tokens automatically unless the user has scrolled away, in which case a
"N new" marker appears. The input keeps a history (up/down on the edge
lines) and stays editable while the agent streams: messages submitted
while busy are queued and sent when the turn ends.

The agent runs on its own asyncio loop in a background thread. It pushes
plain dict events through the ``renderer`` hook (a callable the TUI
installs on the agent); the curses loop drains the event queue every tick
and redraws, so tokens appear live.

Event contract (dicts pushed by the agent's renderer hook):
    {"type": "user", "text": str}
    {"type": "system", "text": str}
    {"type": "response_start"}
    {"type": "reasoning_delta", "text": str}
    {"type": "message_delta", "text": str}
    {"type": "tool_call", "call_id": str, "name": str, "arguments": str}
    {"type": "tool_call_args_delta", "call_id": str, "text": str}
    {"type": "tool_result", "call_id": str, "name": str, "ok": bool,
     "result": any, "message": str | None}
    {"type": "turn_complete"}
    {"type": "error", "text": str}
    {"type": "cancelled"}

The wrapping / input / pane logic below (wrap_spans, TextInput, MessagePane)
is pure Python and has no curses dependency, so it can be exercised
headless (see src/helpers/tui_test.py).
"""

import asyncio
import curses
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path

from config.updater import update_config_file

TICK_MS = 60  # getch timeout; drives the redraw tick
MAX_INPUT_LINES = 5  # input box growth limit
RESULT_PREVIEW_CHARS = 600  # tool result preview cap
ESC_TIMEOUT = 0.5  # seconds to wait for a key following ESC


# ---------------------------------------------------------------------------
# wrapping
# ---------------------------------------------------------------------------


def wrap_spans(text: str, width: int) -> list[tuple[str, int, int]]:
    """Word-wrap ``text`` to ``width`` columns.

    Returns a list of ``(line, start_col, end_col)`` spans. ``start_col`` /
    ``end_col`` are column ranges within the original line (end exclusive),
    which lets the input box map its cursor onto wrapped display rows.
    Words longer than the width are hard-broken; blank input lines yield a
    single empty span. Newlines force a break.
    """
    if width < 1:
        width = 1

    spans: list[tuple[str, int, int]] = []

    for raw in text.split("\n"):
        if raw == "":
            spans.append(("", 0, 0))
            continue

        emitted = False
        start = 0
        n = len(raw)

        while start < n:
            while start < n and raw[start] == " ":
                start += 1
            if start >= n:
                break

            if n - start <= width:
                spans.append((raw[start:].rstrip(" "), start, n))
                emitted = True
                break

            end = start + width
            if raw[end] == " ":
                # the window ends exactly on a word boundary
                cut = end
            else:
                sp = raw[start:end].rfind(" ")
                cut = end if sp <= 0 else start + sp + 1

            spans.append((raw[start:cut].rstrip(" "), start, cut))
            emitted = True
            start = cut

        if not emitted:
            # whitespace-only line: keep one empty row so the cursor has a
            # display row to live on
            spans.append(("", 0, 0))

    return spans


def hard_wrap(text: str, width: int) -> list[str]:
    """Wrap ``text`` to ``width`` columns, returning plain lines."""
    return [line for line, _s, _e in wrap_spans(text, width)]


# ---------------------------------------------------------------------------
# message pane
# ---------------------------------------------------------------------------


class Block:
    """One rendered message unit in the pane."""

    # kind: "user" | "message" | "reasoning" | "tool" | "error" | "system"
    def __init__(self, kind: str, text: str = ""):
        self.kind = kind
        self.text = text
        # tool-call fields
        self.name = ""
        self.args = ""
        self.call_id = ""
        self.ok = None  # None = running, True = ok, False = failed
        self.result = ""  # preview text, filled when the result arrives
        self._cache_key = None
        self._cache: list[str] = []

    def append(self, text: str):
        self.text += text
        self._cache_key = None

    def append_args(self, text: str):
        self.args += text
        self._cache_key = None

    def lines(self, width: int) -> list[str]:
        """Render the block to wrapped display lines (cached per width)."""
        if width < 2:
            width = 2

        key = (width, self.kind, self.text, self.args, self.ok, self.result)
        if self._cache_key == key:
            return self._cache

        if self.kind == "user":
            ls = hard_wrap("> " + self.text, width)
        elif self.kind == "reasoning":
            body = hard_wrap(self.text, max(1, width - 2))
            ls = ["* thinking"]
            ls.extend("| " + line for line in body)
        elif self.kind == "tool":
            head = "+ " + self.name
            if self.ok is True:
                head += "  ok"
            elif self.ok is False:
                head += "  FAIL"
            if self.args:
                head += "  " + self.args
            ls = hard_wrap(head, width)
            if self.result:
                ls.append("")
                ls.extend(hard_wrap(self.result, width))
        elif self.kind == "error":
            ls = hard_wrap("! " + self.text, width)
        else:
            ls = hard_wrap(self.text, width)

        self._cache = ls
        self._cache_key = key
        return ls


class MessagePane:
    """The scrollable message area.

    ``scroll`` counts display rows hidden *below* the bottom edge of the
    viewport, i.e. distance from the bottom: 0 means pinned to the latest
    content (auto-follow). Scrolling up sets it > 0; new content then
    accumulates below the viewport and is reported as "N new".
    """

    def __init__(self):
        self.blocks: list[Block] = []
        self.scroll = 0
        self.follow = True
        self.attrs: dict = {}
        self._version = 0
        self._height = 0
        self._cache = None  # (width, version) -> rows
        self._closed = False  # force the next extend_or_new to start fresh

    def bump(self):
        self._version += 1

    def append(self, block: Block):
        self.blocks.append(block)
        self._closed = False
        self.bump()

    def close_open(self):
        """Mark open blocks as finished so the next reasoning/message of the
        same kind starts a new block (one per LLM response)."""
        self._closed = True

    def extend_or_new(self, kind: str) -> Block:
        """Extend the last block of the same kind, else start a new one."""
        if self._closed:
            self._closed = False
        elif self.blocks:
            last = self.blocks[-1]
            if last.kind == kind and kind in ("reasoning", "message"):
                return last
        block = Block(kind)
        self.blocks.append(block)
        return block

    def last_tool(self) -> Block | None:
        for block in reversed(self.blocks):
            if block.kind == "tool":
                return block
        return None

    def find_tool(self, call_id: str) -> Block | None:
        for block in reversed(self.blocks):
            if block.kind == "tool" and block.call_id == call_id:
                return block
        return None

    def _display(self, width: int) -> list[tuple[str, Block | None]]:
        key = (width, self._version)
        if self._cache is not None and self._cache[0] == key:
            return self._cache[1]

        rows: list[tuple[str, Block | None]] = []
        for block in self.blocks:
            for line in block.lines(width):
                rows.append((line, block))
            rows.append(("", None))  # blank spacer after each block

        self._cache = (key, rows)
        return rows

    def scroll_up(self, rows: int):
        self.follow = False
        self.scroll += rows

    def scroll_down(self, rows: int):
        self.scroll -= rows
        if self.scroll <= 0:
            self.scroll = 0
            self.follow = True

    def page_rows(self) -> int:
        return max(1, self._height - 2)

    def render(self, win, height: int, width: int, attrs: dict):
        self.attrs = attrs
        self._height = height

        rows = self._display(width)
        max_scroll = max(0, len(rows) - height)
        self.scroll = max(0, min(self.scroll, max_scroll))
        if self.follow:
            self.scroll = 0

        win.erase()
        total = len(rows)
        # top-aligned when the content fits, otherwise windowed from the
        # bottom minus the scroll offset
        start = 0 if total <= height else total - height - self.scroll
        for i in range(height):
            idx = start + i
            if 0 <= idx < total:
                text, block = rows[idx]
                if text:
                    self._putstr(win, i, text, self._attr_for(block), width)

        hidden = len(rows) - height - self.scroll
        if hidden > 0:
            label = f" {hidden} new "
            self._putstr(
                win,
                height - 1,
                " " * (width - len(label)) + label,
                attrs.get("dim", 0),
                width,
            )

        win.noutrefresh()

    def _attr_for(self, block: Block | None):
        if block is None:
            return 0
        a = self.attrs
        if block.kind == "tool":
            if block.ok is True:
                return a.get("tool_ok", 0)
            if block.ok is False:
                return a.get("tool_fail", 0)
            return a.get("tool_running", 0)
        return a.get(block.kind, 0)

    @staticmethod
    def _putstr(win, row: int, text: str, attr: int, width: int, col: int = 0):
        if not text:
            return
        avail = width - col
        if avail <= 1:
            return
        text = text[: avail - 1]
        try:
            win.addnstr(row, col, text, len(text), attr)
        except curses.error:
            pass


# ---------------------------------------------------------------------------
# input box
# ---------------------------------------------------------------------------


class TextInput:
    """A multi-line input buffer with wrapping, a 5-line viewport and
    up/down history navigation.

    The buffer is stored as logical lines; display rows are computed by
    wrapping each line to the box width. The viewport (``view_top``) keeps
    the cursor row visible, so text scrolled out of the 5-line window is
    hidden but reachable with the cursor (pi-style overflow).
    """

    def __init__(self):
        self.lines: list[str] = [""]
        self.line = 0  # logical cursor line
        self.col = 0  # cursor column within the logical line
        self.view_top = 0  # first display row shown in the box
        self.history: list[str] = []
        self.hist_idx: int | None = None
        self._draft: list[str] | None = None
        self._draft_cursor: tuple[int, int] | None = None
        self._cache_key = None
        self._cache: list[tuple[str, int, int, int]] = []

    # -- buffer ----------------------------------------------------------

    def text(self) -> str:
        return "\n".join(self.lines)

    def _display(self, width: int) -> list[tuple[str, int, int, int]]:
        """Wrapped rows as (piece, logical_line, start_col, end_col)."""
        key = (width, tuple(self.lines))
        if self._cache_key != key:
            disp = []
            for i, line in enumerate(self.lines):
                for piece, s, e in wrap_spans(line, width):
                    disp.append((piece, i, s, e))
            self._cache_key = key
            self._cache = disp
        return self._cache

    def height(self, width: int) -> int:
        return min(max(len(self._display(width)), 1), MAX_INPUT_LINES)

    def _cursor_pos(self, width: int) -> tuple[int, int]:
        """(display_row, col_in_piece) for the logical cursor."""
        disp = self._display(width)
        row = None
        for idx, (piece, li, s, e) in enumerate(disp):
            if li == self.line and self.col < e:
                row = idx
                break
        if row is None:
            row = max(
                i for i, (_p, li, _s, _e) in enumerate(disp) if li == self.line
            )
        piece, _li, s, _e = disp[row]
        col = max(0, min(self.col - s, len(piece)))
        return row, col

    def _sync_view(self, width: int):
        disp = self._display(width)
        height = min(len(disp), MAX_INPUT_LINES)
        row, _ = self._cursor_pos(width)
        if row < self.view_top:
            self.view_top = row
        if row >= self.view_top + height:
            self.view_top = row - height + 1
        self.view_top = max(0, min(self.view_top, max(0, len(disp) - height)))

    # -- editing ----------------------------------------------------------

    def insert(self, ch: str, width: int):
        line = self.lines[self.line]
        self.lines[self.line] = line[: self.col] + ch + line[self.col :]
        self.col += 1
        self._sync_view(width)

    def newline(self, width: int):
        line = self.lines[self.line]
        left, right = line[: self.col], line[self.col :]
        self.lines[self.line] = left
        self.lines.insert(self.line + 1, right)
        self.line += 1
        self.col = 0
        self._sync_view(width)

    def backspace(self, width: int):
        if self.col > 0:
            line = self.lines[self.line]
            self.lines[self.line] = line[: self.col - 1] + line[self.col :]
            self.col -= 1
        elif self.line > 0:
            right = self.lines.pop(self.line)
            self.line -= 1
            self.lines[self.line] += right
            self.col = len(self.lines[self.line])
        self._sync_view(width)

    def delete(self, width: int):
        line = self.lines[self.line]
        if self.col < len(line):
            self.lines[self.line] = line[: self.col] + line[self.col + 1 :]
        elif self.line < len(self.lines) - 1:
            self.lines[self.line] += self.lines.pop(self.line + 1)
        self._sync_view(width)

    def move(self, dx: int, dy: int, width: int):
        if dx:
            self.col = max(0, min(len(self.lines[self.line]), self.col + dx))
        elif dy:
            self.line = max(0, min(len(self.lines) - 1, self.line + dy))
            self.col = min(self.col, len(self.lines[self.line]))
        self._sync_view(width)

    def line_start(self, width: int):
        self.col = 0
        self._sync_view(width)

    def line_end(self, width: int):
        self.col = len(self.lines[self.line])
        self._sync_view(width)

    def kill_line_start(self, width: int):
        line = self.lines[self.line]
        self.lines[self.line] = line[self.col :]
        self.col = 0
        self._sync_view(width)

    def kill_line_end(self, width: int):
        line = self.lines[self.line]
        self.lines[self.line] = line[: self.col]
        self._sync_view(width)

    def kill_word(self, width: int):
        line = self.lines[self.line]
        c = self.col
        while c > 0 and line[c - 1] == " ":
            c -= 1
        while c > 0 and (line[c - 1].isalnum() or line[c - 1] in "._/-"):
            c -= 1
        self.lines[self.line] = line[:c] + line[self.col :]
        self.col = c
        self._sync_view(width)

    # -- history ----------------------------------------------------------

    def history_up(self, width: int) -> bool:
        if not self.history:
            return False
        if self.hist_idx is None:
            self._draft = list(self.lines)
            self._draft_cursor = (self.line, self.col)
            self.hist_idx = len(self.history)
        if self.hist_idx > 0:
            self.hist_idx -= 1
            self._load_history(self.hist_idx, width)
            return True
        return False

    def history_down(self, width: int) -> bool:
        if self.hist_idx is None:
            return False
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self._load_history(self.hist_idx, width)
        else:
            self._restore_draft(width)
        return True

    def _load_history(self, idx: int, width: int):
        self.lines = self.history[idx].split("\n")
        self.line = len(self.lines) - 1
        self.col = len(self.lines[-1])
        self._sync_view(width)

    def _restore_draft(self, width: int):
        self.hist_idx = None
        self.lines = self._draft or [""]
        self.line, self.col = self._draft_cursor or (0, 0)
        self._draft = None
        self._sync_view(width)

    def commit(self) -> str:
        """Push the buffer to history, clear it, return the submitted text."""
        text = self.text()
        if text.strip():
            self.history.append(text)
        self.lines = [""]
        self.line = 0
        self.col = 0
        self.view_top = 0
        self.hist_idx = None
        self._draft = None
        self._cache_key = None
        return text


# ---------------------------------------------------------------------------
# the TUI
# ---------------------------------------------------------------------------


class CursesTUI:
    """Drive ``agent`` (anything with ``step`` / ``save_session`` /
    ``get_context``) inside a curses screen.

    Install ``agent.renderer = tui._on_event`` implicitly; the agent calls
    it from its async context, and events are relayed into the curses
    thread through a thread-safe queue.
    """

    def __init__(self, agent, model_id: str = "", workspace: str = ""):
        self.agent = agent
        self.model_id = model_id
        self.workspace = workspace

        self.pane = MessagePane()
        self.input = TextInput()

        self.busy = False
        self.status = "idle"
        self.pending: list[str] = []

        self.flash_msg = ""
        self.flash_until = 0.0

        self._q: queue.Queue = queue.Queue()
        self._loop = None
        self._task = None
        self._esc = None  # None | "" (waiting for '[') | str (sequence so far)
        self._esc_t = 0.0
        self._x10 = 0  # X10 mouse data bytes left to swallow
        self._last_width = 80
        self._inner_w = 78  # input wrap width, updated on every draw
        self._pane_h = 1

        agent.renderer = self._on_event
        self._seed_context()

    # -- event plumbing (called from the agent's async context) -----------

    def _on_event(self, event: dict):
        self._q.put(event)

    def _start_step(self, text: str):
        self.busy = True
        self.status = "thinking"
        self._task = asyncio.run_coroutine_threadsafe(
            self.agent.step(text), self._loop
        )
        self._task.add_done_callback(self._on_task_done)

    def _on_task_done(self, fut):
        # Runs on the agent loop thread: only queue events.
        try:
            if fut.cancelled():
                self._q.put({"type": "cancelled"})
            else:
                exc = fut.exception()
                if exc is not None:
                    self._q.put(
                        {"type": "error", "text": f"{type(exc).__name__}: {exc}"}
                    )
                    self._q.put({"type": "turn_complete"})
        except Exception:
            pass

    def _finish_turn(self):
        self.busy = False
        self.status = "idle"
        try:
            self.agent.save_session()
        except Exception:
            pass
        if self.pending:
            self._start_step(self.pending.pop(0))

    def _interrupt(self):
        if self._task is not None and not self._task.done():
            self._loop.call_soon_threadsafe(self._task.cancel)
            self.status = "interrupting"

    def _apply(self, ev: dict):
        t = ev.get("type")
        p = self.pane

        if t == "user":
            p.close_open()
            p.append(Block("user", ev.get("text", "")))
        elif t == "system":
            p.append(Block("system", ev.get("text", "")))
        elif t == "response_start":
            p.close_open()
        elif t == "reasoning_delta":
            p.extend_or_new("reasoning").append(ev.get("text", ""))
        elif t == "message_delta":
            p.extend_or_new("message").append(ev.get("text", ""))
        elif t == "tool_call":
            block = Block("tool")
            block.name = ev.get("name", "?")
            block.args = ev.get("arguments", "")
            block.call_id = ev.get("call_id", "")
            p.append(block)
            self.status = f"running {block.name}"
        elif t == "tool_call_args_delta":
            block = p.last_tool()
            if block is not None:
                block.append_args(ev.get("text", ""))
        elif t == "tool_result":
            block = p.find_tool(ev.get("call_id", "")) or p.last_tool()
            if block is not None:
                block.ok = bool(ev.get("ok"))
                block.result = self._result_preview(ev)
                self.status = f"{block.name} {'ok' if block.ok else 'failed'}"
        elif t == "turn_complete":
            self._finish_turn()
        elif t == "cancelled":
            p.append(Block("system", "(interrupted)"))
            self._finish_turn()
        elif t == "error":
            p.append(Block("error", ev.get("text", "")))
            self.status = "error"
            self._finish_turn()

        p.bump()

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _stringify(value) -> str:
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, indent=2)
        except Exception:
            return str(value)

    def _result_preview(self, ev: dict) -> str:
        if ev.get("ok"):
            preview = self._stringify(ev.get("result"))
        else:
            message = str(ev.get("message") or "").strip()
            result = self._stringify(ev.get("result")).strip()
            preview = "\n".join(x for x in (message, result) if x)
        if len(preview) > RESULT_PREVIEW_CHARS:
            preview = preview[:RESULT_PREVIEW_CHARS] + "..."
        return preview

    def _seed_context(self):
        """Rebuild the pane from a resumed session's context."""
        try:
            context = self.agent.get_context()
        except Exception:
            return

        tool_blocks: dict = {}
        for item in context:
            t = item.get("type", "message")
            if t == "message":
                role = item.get("role")
                if role == "user":
                    self.pane.append(Block("user", item["content"][0]["text"]))
                elif role == "assistant":
                    self.pane.append(Block("message", item["content"][0]["text"]))
            elif t == "function_call":
                block = Block("tool")
                block.name = item.get("name", "?")
                block.args = item.get("arguments") or ""
                block.call_id = item.get("call_id", "")
                tool_blocks[block.call_id] = block
                self.pane.append(block)
            elif t == "function_call_output":
                block = tool_blocks.get(item.get("call_id", ""))
                if block is None:
                    continue
                output = item.get("output", "")
                try:
                    envelope = json.loads(output)
                except Exception:
                    envelope = None
                if isinstance(envelope, dict) and "status" in envelope:
                    block.ok = envelope.get("status") == "ok"
                    if block.ok:
                        block.result = self._stringify(envelope.get("result"))
                    else:
                        message = str(envelope.get("message") or "").strip()
                        result = self._stringify(envelope.get("result")).strip()
                        block.result = "\n".join(x for x in (message, result) if x)
                else:
                    block.ok = True
                    block.result = str(output)
                if len(block.result) > RESULT_PREVIEW_CHARS:
                    block.result = block.result[:RESULT_PREVIEW_CHARS] + "..."

    def _flash(self, message: str):
        self.flash_msg = message
        self.flash_until = time.monotonic() + 2.5

    # -- user input -----------------------------------------------------------

    def _handle_submit(self):
        text = self.input.text()
        stripped = text.strip()
        if not stripped:
            return

        if stripped in ("/bye", "/exit", "/quit"):
            self._quit = True
            return

        if stripped.startswith("/config"):
            parts = stripped.split()
            if len(parts) >= 3:
                try:
                    devnull = open(os.devnull, "w")
                    try:
                        stdout, sys.stdout = sys.stdout, devnull
                        update_config_file(parts[1], parts[2])
                    finally:
                        sys.stdout = stdout
                        devnull.close()
                    self._flash(f"config: {parts[1]} = {parts[2]}")
                except Exception as e:
                    self._flash(f"config error: {e}")
            else:
                self._flash("usage: /config key value")
            self.input.commit()
            return

        if stripped.startswith("/prompt"):
            parts = stripped.split()
            if len(parts) >= 2:
                path = Path(parts[-1]).expanduser().resolve()
                if path.exists():
                    self.input.commit()
                    self._start_step(path.read_text())
                    return
                self._flash(f"no such file: {path}")
            else:
                self._flash("usage: /prompt <file>")
            return

        if stripped.startswith("/save"):
            try:
                self.agent.save_session()
                self._flash("session saved")
            except Exception as e:
                self._flash(f"save failed: {e}")
            self.input.commit()
            return

        if stripped.startswith("/help"):
            self._flash(
                "enter send, esc+enter newline, up/down history, "
                "pgup/pgdn scroll, ctrl+c interrupt/quit"
            )
            return

        # regular message
        self.input.commit()
        if self.busy:
            self.pending.append(stripped)
            self._flash("agent busy, message queued")
        else:
            self._start_step(stripped)

    def _handle_key(self, ch: int):
        ti = self.input
        w = self._inner_w

        if ch in (8, 127, curses.KEY_BACKSPACE):
            ti.backspace(w)
        elif ch == 11:  # ctrl+k
            ti.kill_line_end(w)
        elif ch == 12:  # ctrl+j (same byte as some terminals' Enter)
            ti.newline(w)
        elif ch == 21:  # ctrl+u
            ti.kill_line_start(w)
        elif ch == 23:  # ctrl+w
            ti.kill_word(w)
        elif ch == curses.KEY_LEFT:
            ti.move(-1, 0, w)
        elif ch == curses.KEY_RIGHT:
            ti.move(1, 0, w)
        elif ch == curses.KEY_UP:
            if not ti.history_up(w):
                ti.move(0, -1, w)
        elif ch == curses.KEY_DOWN:
            if not ti.history_down(w):
                ti.move(0, 1, w)
        elif ch == curses.KEY_HOME:
            ti.line_start(w)
        elif ch == curses.KEY_END:
            ti.line_end(w)
        elif ch == curses.KEY_DC:
            ti.delete(w)
        elif 32 <= ch <= 126:
            ti.insert(chr(ch), w)
        elif ch >= 128:  # multi-byte unicode from the terminal
            try:
                ti.insert(chr(ch), w)
            except Exception:
                pass

    # -- curses -----------------------------------------------------------------

    def _init_colors(self) -> dict:
        attrs = {}
        if not curses.has_colors():
            return attrs

        curses.start_color()
        try:
            curses.use_default_colors()
            bg = -1
        except curses.error:
            bg = curses.COLOR_BLACK

        curses.init_pair(1, curses.COLOR_WHITE, bg)  # assistant content
        curses.init_pair(2, curses.COLOR_WHITE, bg)  # dim (paired with A_DIM)
        curses.init_pair(3, curses.COLOR_WHITE, bg)  # blocks w/ grey bg
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(6, curses.COLOR_YELLOW, bg)
        curses.init_pair(7, curses.COLOR_CYAN, bg)

        grey_bg = curses.color_pair(3) | curses.A_DIM

        attrs = {
            "user": grey_bg,
            "reasoning": curses.color_pair(2) | curses.A_DIM,
            "message": curses.color_pair(1),
            "system": curses.color_pair(2) | curses.A_DIM,
            "error": curses.color_pair(5) | curses.A_BOLD,
            "tool_running": grey_bg,
            "tool_ok": curses.color_pair(4) | curses.A_BOLD,
            "tool_fail": curses.color_pair(5) | curses.A_BOLD,
            "dim": curses.color_pair(2) | curses.A_DIM,
            "flash": curses.color_pair(6) | curses.A_BOLD,
            "busy": curses.color_pair(7) | curses.A_BOLD,
            "placeholder": curses.color_pair(2) | curses.A_DIM,
            "border": curses.color_pair(2) | curses.A_DIM,
        }
        return attrs

    def _banner(self):
        parts = ["no-slop"]
        if self.model_id:
            parts.append(f"model: {self.model_id}")
        parts.append(f"workspace: {self.workspace}")
        try:
            sid = self.agent.session_id
            if sid:
                parts.append(f"session: {sid}")
        except Exception:
            pass
        self.pane.append(Block("system", "  |  ".join(parts)))

    def run(self):
        loop = asyncio.new_event_loop()
        self._loop = loop
        worker = threading.Thread(target=loop.run_forever, daemon=True)
        worker.start()

        try:
            curses.wrapper(self._main)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            sys.stderr.write(f"tui error: {e}\n")
        finally:
            if self._task is not None and not self._task.done():
                try:
                    self._task.cancel()
                except Exception:
                    pass
            loop.call_soon_threadsafe(loop.stop)
            worker.join(timeout=3)

    def _main(self, stdscr):
        stdscr.keypad(True)
        curses.noecho()
        curses.cbreak()
        stdscr.timeout(TICK_MS)
        try:
            curses.mousemask(curses.ALL_MOUSE_EVENTS)
        except curses.error:
            pass
        try:
            curses.curs_set(2)
        except (curses.error, TypeError):
            pass

        attrs = self._init_colors()
        self._banner()

        self._quit = False
        # wheel constants are ncurses-version dependent: recent builds
        # (6.5+) dropped MOUSE_WHEEL* entirely and report wheel turns as
        # button 4/5 pressed, so prefer the constants and fall back to
        # those button bits; ancient builds expose neither and simply
        # have no wheel support instead of crashing on the first event
        wheel_up = (getattr(curses, "MOUSE_WHEEL_UP", None)
                    or getattr(curses, "BUTTON4_PRESSED", 0))
        wheel_down = (getattr(curses, "MOUSE_WHEEL_DOWN", None)
                      or getattr(curses, "BUTTON5_PRESSED", 0))

        while not self._quit:
            # drain agent events
            try:
                while True:
                    self._apply(self._q.get_nowait())
            except queue.Empty:
                pass

            # a lone ESC older than ESC_TIMEOUT acts on its own
            if self._esc is not None and time.monotonic() - self._esc_t > ESC_TIMEOUT:
                if self._esc == "":
                    if self.busy:
                        self._interrupt()
                self._esc = None

            self._draw(stdscr, attrs)

            ch = stdscr.getch()
            if ch == -1:
                continue

            if ch == curses.KEY_MOUSE:
                try:
                    _id, _x, _y, _z, btn = curses.getmouse()
                except curses.error:
                    continue
                if wheel_up and btn & wheel_up:
                    self.pane.scroll_up(3)
                elif wheel_down and btn & wheel_down:
                    self.pane.scroll_down(3)
                continue

            # X10 mouse reports that this ncurses does not parse itself
            # arrive as a leaked "[M" sequence plus three coordinate bytes;
            # swallow them so they are never typed into the input
            if self._x10:
                self._x10 -= 1
                continue

            # escape disambiguation: a '[' following ESC starts a sequence
            # we may decode (shift+enter CSI u); CSI sequences close on
            # their final byte (0x40-0x7E) and are dropped unless known;
            # anything else is a lone ESC
            if self._esc is not None:
                if self._esc == "":
                    if ch == 91:  # '['
                        self._esc = "["
                        continue
                    # lone ESC: interrupts when busy, then process ch
                    if self.busy:
                        self._interrupt()
                    self._esc = None
                else:
                    self._esc += chr(ch)
                    if self._esc == "[13;2u":  # shift+enter
                        self._esc = None
                        self.input.newline(self._inner_w)
                        continue
                    if 0x40 <= ch <= 0x7E:  # final byte: sequence is over
                        if self._esc == "[M":  # X10 mouse report
                            self._x10 = 3
                        self._esc = None
                        continue
                    if len(self._esc) > 32:
                        self._esc = None  # not a sequence we know
                        # fall through to normal handling of ch
                    else:
                        continue  # still inside the sequence: swallow ch

            if ch == 27:  # ESC
                self._esc = ""
                self._esc_t = time.monotonic()
                continue

            if ch == 3:  # ctrl+c
                if self.busy:
                    self._interrupt()
                else:
                    self._quit = True
                continue

            if ch == 4:  # ctrl+d
                self._quit = True
                continue

            if ch in (10, 13):  # enter
                self._handle_submit()
                continue

            if ch == curses.KEY_PPAGE:
                self.pane.scroll_up(self.pane.page_rows())
                continue

            if ch == curses.KEY_NPAGE:
                self.pane.scroll_down(self.pane.page_rows())
                continue

            self._handle_key(ch)

    def _hint(self, attrs: dict) -> tuple[str, int, str]:
        if self.flash_msg and time.monotonic() < self.flash_until:
            right = "esc interrupt" if self.busy else ""
            return self.flash_msg, attrs.get("flash", 0), right
        if self.busy:
            right = "esc interrupt"
            if self.pending:
                right += f"  |  {len(self.pending)} queued"
            return f"* {self.status}", attrs.get("busy", 0), right
        return (
            "idle",
            attrs.get("dim", 0),
            "enter send, esc+enter newline, up/down history, "
            "pgup/pgdn scroll, ctrl+c quit",
        )

    def _draw(self, stdscr, attrs: dict):
        h, w = stdscr.getmaxyx()
        self._last_width = w

        if h < 8 or w < 20:
            stdscr.erase()
            msg = "terminal too small, please resize the window"
            try:
                stdscr.addstr(0, 0, msg)
            except curses.error:
                pass
            stdscr.noutrefresh()
            curses.doupdate()
            return

        ti = self.input
        inner_w = max(2, w - 2)
        input_h = ti.height(inner_w)
        box_h = input_h + 2
        pane_h = max(1, h - box_h - 1)
        self._pane_h = pane_h
        hint_y = h - box_h - 1
        box_y = h - box_h

        # status/hint row (drawn on stdscr first, pane and box overwrite)
        stdscr.erase()
        left, left_attr, right = self._hint(attrs)
        self.pane._putstr(stdscr, hint_y, left, left_attr, w)
        if right:
            col = max(0, w - len(right) - 1)
            self.pane._putstr(stdscr, hint_y, right, attrs.get("dim", 0), w, col=col)
        stdscr.noutrefresh()

        # message pane
        pane_win = curses.newwin(pane_h, w, 0, 0)
        self.pane.render(pane_win, pane_h, w, attrs)

        # input box
        box_win = curses.newwin(box_h, w, box_y, 0)
        box_win.erase()
        try:
            box_win.attron(attrs.get("border", 0))
        except curses.error:
            pass
        box_win.border()
        try:
            box_win.attroff(attrs.get("border", 0))
        except curses.error:
            pass

        disp = ti._display(inner_w)
        empty = all(line == "" for line in ti.lines)
        for i in range(input_h):
            d = ti.view_top + i
            if d >= len(disp):
                break
            piece, li, s, e = disp[d]
            if piece:
                self.pane._putstr(
                    box_win, 1 + i, piece, attrs.get("message", 0), w, col=1
                )
            elif empty and i == 0:
                self.pane._putstr(
                    box_win,
                    1 + i,
                    "type a message   (enter send, esc+enter newline)",
                    attrs.get("placeholder", 0),
                    w,
                    col=1,
                )

        # position the hardware cursor at the input cursor
        row, col = ti._cursor_pos(inner_w)
        ry = 1 + (row - ti.view_top)
        ry = max(1, min(box_h - 2, ry))
        cx = max(1, min(1 + col, w - 2))
        box_win.move(ry, cx)  # hardware cursor follows the last noutrefresh
        box_win.noutrefresh()

        curses.doupdate()


def main():
    """Small demo: run the TUI with a fake streaming agent (no LLM needed)."""

    class FakeAgent:
        def __init__(self):
            self.renderer = None
            self.session_id = "demo"
            self.saved = 0

        async def step(self, message: str):
            r = self.renderer
            r({"type": "user", "text": message})
            r({"type": "response_start"})
            for tok in "let me think about that. i will use a tool. ":
                r({"type": "reasoning_delta", "text": tok})
                await asyncio.sleep(0.03)
            r(
                {
                    "type": "tool_call",
                    "call_id": "call_demo",
                    "name": "shell",
                    "arguments": "",
                }
            )
            for tok in '{"command": "echo hello from the fake agent"}':
                r({"type": "tool_call_args_delta", "call_id": "call_demo", "text": tok})
                await asyncio.sleep(0.01)
            await asyncio.sleep(0.3)
            r(
                {
                    "type": "tool_result",
                    "call_id": "call_demo",
                    "name": "shell",
                    "ok": True,
                    "result": "hello from the fake agent",
                    "message": None,
                }
            )
            await asyncio.sleep(0.1)
            for tok in "Here is what i found for you. ":
                r({"type": "message_delta", "text": tok})
                await asyncio.sleep(0.03)
            r({"type": "turn_complete"})

        def save_session(self):
            self.saved += 1

        def get_context(self):
            return []

    CursesTUI(FakeAgent(), model_id="fake-model", workspace=os.getcwd()).run()


if __name__ == "__main__":
    main()
