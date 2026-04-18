from textual.app import App, ComposeResult
from textual import events
from textual.widgets import Header, Footer


class Shell(App):
    TITLE = "no-slop"
    SUB_TITLE = "AI Coding Agent Programmed Without AI"

    CSS_PATH = "textual_shell.tcss"

    def on_mount(self) -> None:
        pass

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()


if __name__ == "__main__":
    app = Shell()
    app.run()
