import curses
from time import sleep

ESCAPE_CHAR = 27


def is_printable_character(key: int) -> bool:
    return key >= 32 and key <= 126


def is_backspace(key: int) -> bool:
    return key == 8 or key == 127 or key == curses.KEY_BACKSPACE


def is_enter_key(key: int) -> bool:
    return key == 10 or key == 13


def tui_app(stdscr):
    curses.curs_set(1)
    curses.start_color()
    curses.noecho()
    curses.cbreak()

    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

    stdscr.keypad(True)
    stdscr.nodelay(True)
    stdscr.bkgd(curses.color_pair(1))

    chat_history = []
    input_buffer = []

    while True:
        stdscr.erase()

        height, width = stdscr.getmaxyx()
        # just allow 1 line for input
        input_y = height - 1
        if input_y < 1:
            input_y = 1

        key = stdscr.getch()

        if key == ESCAPE_CHAR:
            break
        elif is_printable_character(key):
            input_buffer.append(chr(key))
        elif is_backspace(key):
            if input_buffer:
                input_buffer.pop()
        elif is_enter_key(key):
            if input_buffer:
                chat_history.append("".join(input_buffer))
                input_buffer = []

        for i, msg in enumerate(chat_history):
            if i < input_y:
                try:
                    stdscr.addstr(i, 0, msg)
                except curses.error:
                    pass

        input_text = "".join(input_buffer)

        try:
            stdscr.addstr(input_y, 0, f"@ {input_text}")
        except curses.error:
            pass

        stdscr.refresh()
        sleep(1 / 60.0)


def main():
    curses.wrapper(tui_app)


if __name__ == "__main__":
    main()
