#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_DIR = "$SCRIPT_DIR/.venv"

python3 -m venv "$VENV_DIR"

"$VENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
"$VENV_DIR/bin/python" -m pip install -e "$SCRIPT_DIR"


node_cmd=$(command -v node || command -v nodejs)
if [ -z "$node_cmd" ]; then
    echo "Node.js not detected. Installing LTS using volta."
    curl -fsSL https://get.volta.sh | bash
    "$HOME/.volta/bin/volta" install node@lts
fi

echo "Done."