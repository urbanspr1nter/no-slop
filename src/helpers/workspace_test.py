import os
from pathlib import Path


def make_real_path(p: str) -> str:
    working_p = p.replace("$HOME", os.getenv("HOME", "$HOME"))

    resolved = Path(working_p).expanduser().resolve()

    return str(resolved)


def main():
    print(make_real_path("."))
    print(make_real_path("~"))
    print(make_real_path("/usr/bin/../bin/../../usr/local"))
    print(make_real_path("$HOME"))
    print(make_real_path("$HOME/models"))


if __name__ == "__main__":
    main()
