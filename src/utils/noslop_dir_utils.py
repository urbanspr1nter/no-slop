import os

from utils.path_utils import get_home_directory

NO_SLOP_DIRECTORY = ".noslop"


def get_noslop_path() -> str:
    home_dir = get_home_directory()

    # Ideally transforms to: /home/username/.noslop
    noslop_abs_dir = f"{home_dir}/{NO_SLOP_DIRECTORY}"

    return noslop_abs_dir


def create_noslop_path_idem() -> bool:
    """Create the .noslop directory if it doesn't exist under home.

    This is idempotent.

    Returns:
        result - True|False depending on what happened.
        - True if directory was created
        - False if directory already exists or something else happened
    """
    noslop_abs_dir = get_noslop_path()

    if not os.path.exists(noslop_abs_dir):
        os.makedirs(noslop_abs_dir, exist_ok=True)

        return True

    return False
