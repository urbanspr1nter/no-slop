import os
import json
from utils.noslop_dir_utils import get_noslop_path


def update_config_file(key: str, value: str):
    noslop_path = get_noslop_path()
    noslop_config_path = f"{noslop_path}/config.json"

    if os.path.exists(noslop_config_path):
        with open(noslop_config_path, "r") as f:
            loaded_config = json.loads(f.read())

        # key is like provider.local.model
        keys = key.split(".")

        # keys=[provider,local], last_key=model
        last_key = keys.pop()

        curr_node = loaded_config
        for k in keys:
            curr_node = curr_node[k]

        curr_node[last_key] = value

        with open(noslop_config_path, "w") as f:
            f.write(json.dumps(loaded_config, indent=2))

        print(
            f"Updated {key} to be {value}. Changes will take effect on the next restart."
        )
