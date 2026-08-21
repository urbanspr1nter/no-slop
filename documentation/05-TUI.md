# TUI

The interactive interface is a single module, `src/interface/curses_tui.py`, drawn with the standard-library `curses` module. There is deliberately no TUI framework: the interface has to stay light, so prompt_toolkit and textual (used by the old UI and by dead experiments in `src/helpers/`) are gone from the entry path and from `setup.py`.

## Layout

The screen has three regions, recomputed every frame:

- **Message pane** (top, all but the last rows): the conversation, rendered as blocks — system banner, user, reasoning, tool, message, error — separated by blank spacers. Content is top-aligned while it fits, then windowed from the bottom so the newest text is visible; `scroll` counts rows hidden below the viewport (0 means pinned/following). Scrolling up shows a "N new" indicator instead of auto-jumping.
- **Hint row** (one row above the box): status on the left (`idle`, `* thinking`, `* running <tool>`, `<tool> ok/failed`, `error`), key hints or a flash message on the right. Flash messages (queued input, config changes, usage errors) hold the left slot for 2.5 s.
- **Input box** (bottom, bordered): the composer. It grows with the content up to 5 display rows, then overflows the pi way — earlier lines are hidden but reachable by moving the text cursor back. Up/down on the top/bottom display row walks the history instead; the in-progress draft is saved and restored on the way back down.

Both the pane and the input box wrap at the inner width (word-greedy via `wrap_spans`, long words hard-broken).

## Threading

`curses.wrapper` runs the main loop on the main thread. The agent runs on a background thread with its own `asyncio` loop; a submission does `asyncio.run_coroutine_threadsafe(agent.step(text), loop)`. `StreamingAgent.step()` accepts an optional `renderer` callback and emits a small dict-based event stream; without a renderer it falls back to the legacy stdout printing, which is what the headless `-p` path uses.

Events cross the thread boundary through a `queue.Queue`. The main loop is tick-driven: `stdscr.timeout(60)` makes `getch()` return after 60 ms, and every tick the loop drains the queue, applies the events to the pane, and redraws. That gives smooth token-by-token streaming while the input box stays fully typeable — the user can keep typing (and queue more messages) while a turn runs.

Event types: `user`, `system`, `response_start`, `reasoning_delta{text}`, `message_delta{text}`, `tool_call{call_id,name,arguments}`, `tool_call_args_delta{call_id,text}`, `tool_result{call_id,name,ok,result,message}`, `turn_complete`, `cancelled`, `error{text}`. One subtlety inherited from the stream processor: in openai 3.x the delta events carry `item_id` but no `call_id`, so the TUI/agent capture the `call_id` from `response.output_item.added` and reuse it for the args deltas.

## Blocks and colors

Each pane block kind renders with a fixed style, eight colors via `use_default_colors`:

- user: `> text` in a dim grey background block.
- reasoning: `* thinking` label with the trace under it as `| …` lines, dim grey.
- tool: `+ name  [ok|FAIL]  <args>` with the args streaming in as they arrive; once the result lands, the line turns green (ok) or red (fail) and a result preview (first 600 chars, JSON pretty-printed when possible) is appended.
- message: white, the normal text.
- error: `! text` in red.

`MessagePane.extend_or_new(kind)` extends the last open reasoning/message block (so a streamed response stays one block); `close_open()` is called at `user` and `response_start` so each LLM response starts fresh.

## Keys and commands

Enter sends, Escape+Enter inserts a newline (a lone Escape interrupts a running turn after a 0.5 s grace, and decodes shift+Enter `CSI u` as a newline), Ctrl+C interrupts when busy / quits when idle, Ctrl+D quits. PgUp/PgDn and the mouse wheel scroll the pane; up/down arrows edit or walk history on the edge rows; Ctrl+U/Ctrl+K/Ctrl+W do the usual line kills.

Commands are plain text sent with Enter: `/bye`, `/exit`, `/quit`, `/help`, `/config <key> <value>` (edits `~/.noslop/config.json` live), `/prompt <file>` (system prompt override), and `/save` (force a session save). A submission while a turn is running is queued — the hint row shows `N queued` and the next turn starts automatically on `turn_complete`. Sessions are also saved automatically after every completed turn, and `--session-resume` reseeds the pane from the persisted context (user/assistant messages plus tool calls matched to their results by `call_id`).

## Mouse and escape handling

`mousemask(ALL_MOUSE_EVENTS)` is set at startup. Wheel turns are matched against masks derived per ncurses version: recent builds (6.5+) dropped the `MOUSE_WHEEL*` constants and report wheel turns as button 4/5 pressed, so the handler prefers the constants and falls back to `BUTTON4_PRESSED`/`BUTTON5_PRESSED`; a build with neither simply has no wheel support instead of crashing on the first mouse event (a bare `curses.MOUSE_WHEEL` reference did exactly that on this machine).

The escape state machine does double duty. A lone ESC interrupts a running turn after a 0.5 s grace; a following `[` starts a sequence that is collected until a CSI final byte (0x40-0x7E) — decoded only for shift+enter (`[13;2u`), dropped otherwise. That also shields the input from raw mouse bytes: this ncurses parses only SGR mouse reports (`?1006` mode), so an X10 report leaks through `getch` as `ESC [ M` plus three coordinate bytes; the machine recognizes the bare `[M` as a mouse report and swallows the three trailing bytes so they never get typed into the box.

## Testing

`src/helpers/tui_test.py` covers it in two parts. Part 1 exercises the pure logic (wrapping, input buffer/viewport/history, pane scroll math) headless. Part 2 runs the real `CursesTUI` in a forked child under a PTY (30x100, `TERM=xterm`) with a fake streaming agent, types two messages (the second while the first turn is busy), and asserts on the rendered screen, including a mouse gauntlet (SGR wheel up/down, SGR click, an unparsed X10 wheel that must be swallowed, and a shift+enter that must grow the input box by exactly one row). Because curses emits only per-frame diffs, the test rebuilds the screen with a minimal VT emulator (`MiniScreen`: CUP/VPA/HPA, ECH, EL/ED, scroll regions — an LF at the region bottom scrolls the region, which is how curses renders the box growing — charset switches) and checks the reconstructed final grid; stream-order checks use markers that are always written contiguously. PTY timing can flake under load, so the e2e retries a bounded number of times; on failure it reports the raw and stripped stream tail, the child's stderr (diverted to a temp file), and the reconstructed screen with row numbers.
