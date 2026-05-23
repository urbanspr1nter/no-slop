import os

from pathlib import Path
from utils.path_utils import get_home_directory

NO_SLOP_DIRECTORY = ".noslop"


def get_noslop_path() -> str:
    home_dir = get_home_directory()
    noslop_abs_dir = f"{home_dir}/{NO_SLOP_DIRECTORY}"

    return noslop_abs_dir


def create_noslop_path_idem() -> bool:
    """Create the .noslop directory if doesn't exist under home.

    This is idempotent.

    Returns:
        result - True|False depending on what happened
            - True if directory was created
            - False if already exists or something else.
    """
    noslop_abs_dir = get_noslop_path()

    if not os.path.exists(noslop_abs_dir):
        os.makedirs(noslop_abs_dir, exist_ok=True)

        return True

    return False


def make_noslop_path(path: str) -> str:
    real_path = Path(f"{get_noslop_path()}/{path}").expanduser().resolve()

    return str(real_path)


def noslop_write_file(contents: str, path: str) -> str:
    dest_path = make_noslop_path(path)

    try:
        with open(dest_path, "w") as f:
            f.write(contents)
    except IOError:
        print(f"Couldn't write {contents} to path: {path}")
        raise


def noslop_read_file(path: str) -> str:
    dest_path = make_noslop_path(path)

    try:
        with open(dest_path, "r") as f:
            contents = f.read()
    except (IOError, FileNotFoundError):
        print(f"File not found error: {contents}")
        raise
