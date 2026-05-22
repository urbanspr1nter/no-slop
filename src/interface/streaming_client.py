import os
import argparse
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from orchestrator.streaming_agent import StreamingAgent
from config.loader import load_config, Config

import asyncio

history = InMemoryHistory()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--system-prompt")

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

    print(f"<system_prompt>\n{system_prompt}\n</system_prompt>")

    config: Config = load_config()
    agent = StreamingAgent(config=config)

    agent.set_system_prompt(system_prompt)

    while True:
        try:
            user_request = await asyncio.to_thread(
                prompt,
                "? ",
                multiline=True,
                history=history,
            )
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

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
