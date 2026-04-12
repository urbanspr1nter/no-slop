from textual.app import App, ComposeResult
from textual.widgets import Input, Static, Header, Footer
from textual.binding import Binding
from textual.message import Message


class Shell(App):
    # Bindings for history nav
    BINDINGS = [
        Binding("up", "previous_command", "Prevous", show=True),
        Binding("down", "next_command", "Next", show=True),
        Binding("enter", "submit_command", "Submit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.history = []
        self.history_index = -1

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Enter command:")
        yield Static("", id="output")
        yield Input(placeholder="...")
        yield Footer()

    def action_submit_command(self):
        input_widget = self.query_one(Input)
        command = input_widget.value

        if command:
            self.history.append(command)
            self.history_index = len(self.history)

            output = self.query_one("#output", Static)
            output.update(f"$ {command}\n[Command executed]")

            input_widget.value = ""

        if command == "exit":
            exit(0)

    def action_previous_command(self):
        pass

    def action_next_command(self):
        pass

    def on_input_submitted(self, event: Input.Submitted):
        self.action_submit_command()


if __name__ == "__main__":
    app = Shell()
    app.run()
