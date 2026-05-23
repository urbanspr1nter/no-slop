import os
import argparse
import datetime
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from orchestrator.streaming_agent import StreamingAgent
from config.loader import load_config, Config
from utils.path_utils import make_real_path

import asyncio

from openai import AsyncOpenAI
from typing import Literal

history = InMemoryHistory()


async def send(client: AsyncOpenAI, context: list):
    current_state: Literal["started", "reasoning", "tool_call", "message"] = "started"

    pass


async def main():
    config: Config = load_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--system-prompt")
    parser.add_argument("-w", "--workspace")

    args = parser.parse_args()

    system_prompt = "You are a helpful assistant."
    if args.system_prompt:
        try:
            if os.path.exists(Path(args.system_prompt).expanduser().resolve()):
                with open(Path(args.system_prompt).expanduser().resolve(), "r") as f:
                    system_prompt = f.read()
            else:
                system_prompt = args.system_prompt
        except:
            system_prompt = args.system_prompt

    if args.workspace:
        if os.path.exists(make_real_path(args.workspace)):
            config.workspace = make_real_path(args.workspace)
        else:
            config.workspace = make_real_path(".")
    else:
        config.workspace = make_real_path(".")

    os.chdir(config.workspace)

    system_prompt += f"""

# Session Information:

- The current workspace directory: {config.workspace}
- The current date (YYYY-MM-dd): {datetime.datetime.today().strftime('%Y-%m-%d')}
"""

    print(f"<system_prompt>\n{system_prompt}\n</system_prompt>")

    agent = StreamingAgent(config=config)

    agent.set_system_prompt(system_prompt)

    while True:
        try:
            user_request = await asyncio.to_thread(
                prompt, "? ", multiline=True, history=history
            )
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        user_request = user_request.strip()
        if not user_request:
            continue

        if user_request == "/bye":
            break
        if user_request.startswith("/prompt"):
            filepath = user_request.split(" ")[-1]
            if os.path.exists(Path(filepath).expanduser().resolve()):
                with open(Path(filepath).expanduser().resolve(), "r") as f:
                    user_request = f.read()

        await agent.step(user_request)


if __name__ == "__main__":
    asyncio.run(main())
