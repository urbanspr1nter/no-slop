"""Ad-hoc tests for the curses TUI (src/interface/curses_tui.py).

Part 1 (logic) exercises the pure wrapping / input / pane state machines
headless, no terminal required. Part 2 (pty) runs the real CursesTUI under
a pseudo-terminal with a fake streaming agent, types messages, and checks
the rendered screen. Because curses only emits the *diff* of each frame,
the test rebuilds the screen with a minimal VT grid emulator
(MiniScreen) and asserts on the final screen state, while a few
contiguous single-write markers are checked in stream order.

Run:  .venv/bin/python src/helpers/tui_test.py
"""

import fcntl
import os
import pty
import re
import select
import struct
import sys
import termios
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

CHILD_ERR_FILE = os.path.join(
    os.environ.get("TMPDIR", "/tmp"), "no-slop-tui-test-child.err"
)


# ---------------------------------------------------------------------------
# part 1: logic
# ---------------------------------------------------------------------------


def test_logic():
    from interface.curses_tui import (
        wrap_spans,
        hard_wrap,
        TextInput,
        MessagePane,
        Block,
    )

    W = 10

    # wrapping
    sp = wrap_spans("aaa bbb ccc", 7)
    assert [s[0] for s in sp] == ["aaa bbb", "ccc"], sp
    assert sp[0][1:] == (0, 7) and sp[1][1:] == (8, 11), sp
    sp = wrap_spans("hello world foo", 8)
    assert [s[0] for s in sp] == ["hello", "world", "foo"], sp
    sp = wrap_spans("abcdefgh", 4)
    assert [s[0] for s in sp] == ["abcd", "efgh"], sp
    assert hard_wrap("a\n\nb", 10) == ["a", "", "b"]
    assert hard_wrap("", 10) == [""]
    assert hard_wrap("   ", 10) == [""]
    assert hard_wrap("  a  ", 10) == ["a"]
    print("  wrap OK")

    # input box: wrapping, growth cap, pi-style overflow viewport
    ti = TextInput()
    for ch in "one two three four":
        ti.insert(ch, W)
    assert ti.text() == "one two three four"
    assert ti.height(W) == 2  # wraps to two display rows

    for i in range(7):
        ti.insert(f"line{i} text", W)
        ti.newline(W)
    assert len(ti.lines) == 8  # 7 lines + trailing empty
    assert ti.height(W) == 5  # capped at MAX_INPUT_LINES
    row, _col = ti._cursor_pos(W)
    assert row == ti.view_top + 4, (row, ti.view_top)  # cursor pinned to bottom
    for _ in range(10):
        ti.move(0, -1, W)
    assert ti.line == 0 and ti.view_top == 0  # navigated back to hidden top

    # history up/down
    ti2 = TextInput()
    ti2.history = ["first cmd", "second cmd"]
    assert ti2.history_up(W)
    assert ti2.text() == "second cmd"
    assert ti2.history_up(W)
    assert ti2.text() == "first cmd"
    assert not ti2.history_up(W)  # at the oldest entry
    assert ti2.history_down(W)
    assert ti2.text() == "second cmd"
    assert ti2.history_down(W)
    assert ti2.text() == "" and ti2.hist_idx is None  # draft restored

    # editing ops
    ti3 = TextInput()
    for ch in "hello world":
        ti3.insert(ch, W)
    ti3.line_end(W)
    ti3.kill_word(W)
    assert ti3.text() == "hello ", repr(ti3.text())
    ti3.backspace(W)
    assert ti3.text() == "hello"
    ti3.line_end(W)
    ti3.newline(W)
    assert ti3.lines == ["hello", ""]
    print("  input OK")

    # pane: blocks, block merging, tool states, scroll math
    p = MessagePane()
    p.append(Block("user", "hi there"))
    b = p.extend_or_new("message")
    b.append("streaming text here ")
    assert p.extend_or_new("message") is b  # same block extends
    p.close_open()
    assert p.extend_or_new("message") is not b  # new response -> new block
    tb = Block("tool")
    tb.name = "shell"
    tb.args = '{"command": "ls"}'
    p.append(tb)
    assert p.last_tool() is tb
    tb.ok = True
    tb.result = "file1.txt"
    p.append(Block("reasoning", "thinking about it"))
    flat = [r[0] for r in p._display(40)]
    assert any(l.startswith("> ") for l in flat)  # user block prefix
    assert any(l == "* thinking" for l in flat)  # reasoning label
    assert any(l == "| thinking about it" for l in flat)  # reasoning body
    assert any(l.startswith("+ shell") for l in flat)
    assert any("file1.txt" in l for l in flat)  # result preview rendered

    p2 = MessagePane()
    for i in range(30):
        p2.append(Block("message", f"msg number {i}"))
    assert p2.scroll == 0 and p2.follow is True
    p2.scroll_up(5)
    assert p2.scroll == 5 and p2.follow is False
    p2.scroll_down(10)
    assert p2.scroll == 0 and p2.follow is True
    print("  pane OK")


# ---------------------------------------------------------------------------
# part 2: pty end-to-end
# ---------------------------------------------------------------------------


class MiniScreen:
    """Just enough VT100/xterm emulation to rebuild the screen state from a
    curses byte stream: CUP / VPA / HPA / relative moves, character and
    line erase, scroll regions with IND / RI, and plain text. SGR, modes,
    and everything else is ignored."""

    def __init__(self, rows=30, cols=100):
        self.rows = rows
        self.cols = cols
        self.grid = [[" "] * cols for _ in range(rows)]
        self.y = 0
        self.x = 0
        self.top = 0
        self.bot = rows - 1
        self.wrap = True

    def put(self, s: str):
        for ch in s:
            if ch == "\n":
                # LF = cursor down + IND: at the region bottom the region
                # scrolls up instead of the cursor moving
                if self.y < self.bot:
                    self.y += 1
                else:
                    self._scroll_region_up(1)
                self.x = 0
            elif ch == "\r":
                self.x = 0
            elif ch == "\b":
                self.x = max(0, self.x - 1)
            elif ch >= " " and ch != "\x7f":
                if self.x >= self.cols:
                    if self.wrap:
                        if self.y < self.bot:
                            self.y += 1
                        else:
                            self._scroll_region_up(1)
                        self.x = 0
                    else:
                        continue
                self.grid[self.y][self.x] = ch
                self.x += 1

    def _scroll_region_up(self, k):
        k = max(0, min(k, self.bot - self.top + 1))
        for y in range(self.top, self.bot - k + 1):
            self.grid[y] = self.grid[y + k][:]
        for y in range(self.bot - k + 1, self.bot + 1):
            self.grid[y] = [" "] * self.cols

    def _scroll_region_down(self, k):
        k = max(0, min(k, self.bot - self.top + 1))
        for y in range(self.bot, self.top + k - 1, -1):
            self.grid[y] = self.grid[y - k][:]
        for y in range(self.top, self.top + k):
            self.grid[y] = [" "] * self.cols

    def _csi(self, params: str, final: str):
        nums = [int(p) for p in params.split(";") if p.isdigit()]
        n = lambda i, d=1: nums[i] if i < len(nums) else d  # noqa: E731
        if final in ("H", "f"):
            self.y = max(0, min(n(0) - 1, self.rows - 1))
            self.x = max(0, min(n(1) - 1, self.cols - 1))
        elif final == "d":  # VPA
            self.y = max(0, min(n(0) - 1, self.rows - 1))
        elif final == "G":  # HPA
            self.x = max(0, min(n(0) - 1, self.cols - 1))
        elif final == "A":
            self.y = max(0, self.y - n(0))
        elif final == "B":
            self.y = min(self.rows - 1, self.y + n(0))
        elif final == "C":
            self.x = min(self.cols - 1, self.x + n(0))
        elif final == "D":
            self.x = max(0, self.x - n(0))
        elif final == "X":  # ECH: erase chars at cursor; cursor does not move
            for i in range(n(0)):
                if self.x + i < self.cols:
                    self.grid[self.y][self.x + i] = " "
        elif final == "r":  # DECSTBM
            self.top = max(0, min(n(0) - 1, self.rows - 1))
            self.bot = max(self.top, min(n(1) - 1, self.rows - 1))
        elif final == "M":  # RI (reverse index)
            if self.y > self.top:
                self.y -= n(0)
            else:
                self._scroll_region_down(min(n(0), self.bot - self.top + 1))
        elif final == "E":  # IND (index)
            if self.y < self.bot:
                self.y += n(0)
            else:
                self._scroll_region_up(min(n(0), self.bot - self.top + 1))
        elif final == "K":
            if nums and nums[0] == 0:
                rng = range(self.x, self.cols)
            elif nums and nums[0] == 1:
                rng = range(0, self.x + 1)
            else:
                rng = range(self.cols)
            for x in rng:
                self.grid[self.y][x] = " "
        elif final == "J":
            if nums and nums[0] == 2:
                self.grid = [[" "] * self.cols for _ in range(self.rows)]
            elif not nums or nums[0] == 0:
                for x in range(self.x, self.cols):
                    self.grid[self.y][x] = " "
                for y in range(self.y + 1, self.rows):
                    for x in range(self.cols):
                        self.grid[y][x] = " "
            elif nums[0] == 1:
                for x in range(0, self.x + 1):
                    self.grid[self.y][x] = " "
                for y in range(0, self.y):
                    for x in range(self.cols):
                        self.grid[y][x] = " "
        elif final == "h" and "?" in params and params == "?7":
            self.wrap = True
        elif final == "l" and params == "?7":
            self.wrap = False
        # all other sequences (SGR, modes, ...) do not affect the grid

    def feed(self, data: bytes):
        text = data.decode("utf-8", "replace")
        i = 0
        while i < len(text):
            c = text[i]
            if c == "\x1b":
                m = re.match(r"\x1b\[([0-9;?]*)([A-Za-z])", text[i:])
                if m:
                    self._csi(m.group(1), m.group(2))
                    i += m.end()
                    continue
                if i + 1 < len(text) and text[i + 1] in "()[*+<>]":
                    i += 3  # charset designation: ESC ( X (curses box drawing)
                    continue
                if i + 1 < len(text) and text[i + 1] == "]":
                    # OSC string, terminated by BEL or ST
                    k = text.find("\x07", i + 2)
                    k2 = text.find("\x1b\\", i + 2)
                    cands = [x for x in (k, k2) if x != -1]
                    end = min(cands) if cands else len(text) - 1
                    i = end + 1 if k in cands and (k2 not in cands or k <= k2) else end + 2
                    continue
                i += 2  # two-byte escape: ESC 7, ESC 8, ESC M, ESC =, ...
                continue
            j = i
            while j < len(text) and text[j] != "\x1b":
                j += 1
            self.put(text[i:j])
            i = j

    def text(self) -> str:
        return "\n".join("".join(row).rstrip() for row in self.grid)


ANSI_RE = re.compile(rb"\x1b(?:\[[0-9;?]*[A-Za-z]|O[A-Za-z]|[=>]|[78MDE])")


def strip_ansi(data: bytes) -> str:
    prev = None
    while prev != data:
        prev = data
        data = ANSI_RE.sub(b"", data)
    return data.decode("utf-8", "replace")


def child_code():
    """Runs inside the forked child: fake agent + real CursesTUI.

    stderr goes to CHILD_ERR_FILE so any traceback survives for the parent
    to report on failure (the pty stream is kept clean for assertions).
    """
    return """
import asyncio, os, sys
sys.path.insert(0, %r)
sys.stderr = open(%r, "w")
sys.stderr.write("child started\\n")

class FakeAgent:
    def __init__(self):
        self.renderer = None
        self.session_id = "e2e-session"
        self.steps = []
        self.saved = 0

    async def step(self, message):
        r = self.renderer
        r({"type": "user", "text": message})
        r({"type": "response_start"})
        await asyncio.sleep(0.05)
        for tok in "checking the file ".split(" "):
            r({"type": "reasoning_delta", "text": tok + " "})
            await asyncio.sleep(0.02)
        r({"type": "tool_call", "call_id": "call_e2e_1", "name": "shell",
           "arguments": ""})
        for chunk in ['{"command": ', '"ls"}']:
            r({"type": "tool_call_args_delta", "call_id": "call_e2e_1",
               "text": chunk})
            await asyncio.sleep(0.05)
        await asyncio.sleep(0.3)
        r({"type": "tool_result", "call_id": "call_e2e_1", "name": "shell",
           "ok": True, "result": "alpha.txt\\nbravo.txt", "message": None})
        await asyncio.sleep(0.05)
        for tok in "here are the files".split(" "):
            r({"type": "message_delta", "text": tok + " "})
            await asyncio.sleep(0.02)
        r({"type": "turn_complete"})
        self.steps.append(message)

    def save_session(self):
        self.saved += 1

    def get_context(self):
        return []

from interface.curses_tui import CursesTUI
CursesTUI(FakeAgent(), model_id="fake-model", workspace=os.getcwd()).run()
sys.stderr.write("run() returned normally\\n")
sys.stderr.flush()
os._exit(0)
""" % (SRC, CHILD_ERR_FILE)


def _stream_context(st: str, needle: str, before: int = 60, after: int = 40) -> str:
    i = st.find(needle)
    if i < 0:
        return f"(no {needle!r} in stream)"
    return repr(st[max(0, i - before):i + after])


def _pty_once(rows: int, cols: int):
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    pid = os.fork()
    if pid == 0:
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(master)
        os.close(slave)
        os.environ["TERM"] = "xterm"
        # explicit namespace so the child's `import asyncio` lands where the
        # exec'd class methods can find it (a bare exec() inside a function
        # scopes imports to the caller's locals, invisible to the methods)
        child_globals: dict = {"__name__": "__tui_child__"}
        exec(  # noqa: S102 - test child
            compile(child_code(), "<tui-child>", "exec"),
            child_globals,
            child_globals,
        )
        os._exit(1)

    os.close(slave)

    screen = MiniScreen(rows, cols)
    stream = []
    child_done = False

    def drain(seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            r, _, _ = select.select([master], [], [], 0.1)
            if r:
                try:
                    data = os.read(master, 65536)
                except OSError:
                    return
                if not data:
                    return
                screen.feed(data)
                stream.append(data)

    def send(data: bytes):
        os.write(master, data)

    def stream_text():
        return strip_ansi(b"".join(stream))

    def diag() -> str:
        """Failure diagnostics: stream tail + child stderr + early exit."""
        parts = [f"--- raw stream tail ---\n{b''.join(stream)[-600:]!r}"]
        parts.append(f"--- stream tail ---\n{stream_text()[-500:]!r}")
        try:
            with open(CHILD_ERR_FILE) as f:
                err = f.read().strip()
            if err:
                parts.append(f"--- child stderr ---\n{err}")
        except OSError:
            pass
        try:
            wpid, status = os.waitpid(pid, os.WNOHANG)
            if wpid == pid:
                parts.append(f"--- child exited early, status {status} ---")
        except ChildProcessError:
            pass
        return "\n".join(parts)

    def fail(label: str):
        raise AssertionError(f"{label}\n{diag()}")

    def screen_fail(label: str):
        numbered = "\n".join(
            f"{i:02d}|{r}" for i, r in enumerate(screen.text().split("\n"))
        )
        fail(f"{label}\n--- final screen (numbered) ---\n{numbered}")

    try:
        if os.path.exists(CHILD_ERR_FILE):
            os.unlink(CHILD_ERR_FILE)

        # initial screen: banner + placeholder
        drain(1.0)
        t = screen.text()
        for needle, label in [
            ("no-slop", "banner"),
            ("fake-model", "model id"),
            ("e2e-session", "session id"),
            ("type a message", "placeholder"),
        ]:
            if needle not in t:
                screen_fail(f"{label} missing")
        print("  initial screen OK")

        # first message, then a second one while the agent is busy
        send(b"hello e2e\r")
        drain(0.35)
        send(b"second message\r")
        drain(2.5)

        # wait until both turns are done AND the 2.5s "message queued"
        # flash has expired, so the hint row is back to its idle text
        # (the flash overwrites the status word, which would otherwise
        # make the "idle" assertion race the flash expiry)
        right_hint = ("enter send, esc+enter newline, up/down history, "
                      "pgup/pgdn scroll, ctrl+c quit")
        deadline = time.monotonic() + 8
        while right_hint not in screen.text() and time.monotonic() < deadline:
            drain(0.1)

        # streaming order, checked on markers each written contiguously
        # (a single addstr, or a suffix appended by the frame diff)
        st = stream_text()
        markers = ["hello e2e", "| checking", '{"command":', "alpha.txt", "here"]
        idx = {m: st.find(m) for m in markers}
        missing = [m for m in markers if idx[m] < 0]
        if missing:
            fail(
                f"stream marker(s) missing: {missing}\n"
                f"--- context ---\n{_stream_context(st, 'shell')}"
            )
        vals = [idx[m] for m in markers]
        if vals != sorted(vals):
            fail(f"stream order wrong: {list(zip(markers, vals))}")
        if "queued" not in st:
            fail("busy queue indicator missing")
        print("  streaming order OK")

        # final screen state (full strings, and block order top to bottom)
        t = screen.text()
        for needle, label in [
            ("> hello e2e", "user block"),
            ("| checking the file", "reasoning trace"),
            ('+ shell  ok  {"command": "ls"}', "tool block (ok state)"),
            ("alpha.txt", "result preview (alpha)"),
            ("bravo.txt", "result preview (bravo)"),
            ("here are the files", "final message"),
            ("> second message", "queued user block"),
            ("idle", "idle status"),
        ]:
            if needle not in t:
                screen_fail(f"{label} missing")
        order = ["> hello e2e", "* thinking", "+ shell", "alpha.txt",
                 "here are the files", "> second message"]
        oidx = {s: t.index(s) for s in order}
        vals = [oidx[s] for s in order]
        if vals != sorted(vals):
            fail(f"block order wrong: {list(zip(order, vals))}")
        print("  final screen OK")

        # mouse: this ncurses parses SGR reports (?1006 mode) — wheel up
        # and down must scroll the pane and back without damage — while
        # X10 reports it does not parse leak into getch as stray bytes and
        # must be swallowed, not typed into the input box
        send(b"\x1b[<64;1;1M")  # SGR wheel up
        drain(0.3)
        send(b"\x1b[<65;1;1M")  # SGR wheel down
        send(b"\x1b[M" + bytes([96, 33, 33]))  # X10 wheel up (unparsed)
        drain(0.3)
        send(b"\x1b[<0;1;1M")  # SGR left click
        drain(0.5)
        t = screen.text()
        if "no-slop" not in t:
            screen_fail("screen damaged after mouse events")
        if "> second message" not in t:
            screen_fail("pane scrolled wrong by wheel events")
        if "type a message" not in t:
            screen_fail("stray mouse bytes typed into the input box")
        print("  mouse events OK")

        # shift+enter (CSI u) must insert a newline and grow the box:
        # the placeholder drops exactly one row when the box gains a line
        send(b"\x1b[13;2u")
        drain(0.5)
        rows = screen.text().split("\n")
        ph = [i for i, r in enumerate(rows) if "type a message" in r]
        if len(ph) != 1 or ph[0] != 27:
            screen_fail(f"shift+enter did not grow the input box (placeholder rows {ph})")
        print("  shift+enter OK")

        # quit
        send(b"/bye\r")
        deadline = time.monotonic() + 8
        status = None
        while time.monotonic() < deadline:
            drain(0.2)
            wpid, wait_status = os.waitpid(pid, os.WNOHANG)
            if wpid == pid:
                status = wait_status
                break
        child_done = status is not None
        if not child_done:
            fail("child did not exit after /bye")
        if not (os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0):
            fail(f"child exited with status {status}")
        print("  quit OK")
    finally:
        if not child_done:
            try:
                os.kill(pid, 9)
                os.waitpid(pid, 0)
            except OSError:
                pass
        try:
            os.close(master)
        except OSError:
            pass


def test_pty():
    # PTY timing can flake under load (tick/drain races), so retry a few
    # times before giving up; each attempt is a full fresh child process.
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            _pty_once(30, 100)
            return
        except AssertionError as e:
            if attempt == attempts:
                raise
            print(f"  attempt {attempt} failed, retrying:\n{e}")


def main():
    print("logic:")
    test_logic()
    print("pty e2e:")
    test_pty()
    print("ALL TUI TESTS PASSED")


if __name__ == "__main__":
    main()
