from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

history = InMemoryHistory()


def main():
    while True:
        try:
            text = prompt(
                "? ",
                multiline=True,
                history=history,
            )
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        print("\nYou said:")
        print(text)

        if text.strip():
            history.append_string(text)


if __name__ == "__main__":
    main()
