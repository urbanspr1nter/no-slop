from textual.app import App, ComposeResult
from textual import events
from textual.widgets import Header, Footer, Static


class Shell(App):
    TITLE = "no-slop"
    SUB_TITLE = "AI Coding Agent Programmed Without AI"

    CSS_PATH = "textual_shell.tcss"

    def on_mount(self) -> None:
        pass

    def compose(self) -> ComposeResult:
        input_field_widget = Static(
            "type something here!",
            classes="input-field",
        )
        input_field_widget.styles.layout = "vertical"

        yield Header()
        yield Static("MessagePane", classes="message-pane")
        yield input_field_widget
        yield Footer()


if __name__ == "__main__":
    app = Shell()
    app.run()
