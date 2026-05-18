import os
import asyncio
import argparse
from pathlib import Path

from orchestrator.agent import Agent
from config.loader import load_config, Config


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
    agent = Agent(config=config)

    agent.set_system_prompt(system_prompt)

    while True:
        user_request = input("? ")

        if user_request == "/bye":
            break
        if user_request.startswith("/prompt"):
            filepath = user_request.split(" ")[-1]
            if os.path.exists(Path(filepath).expanduser().resolve()):
                with open(Path(filepath).expanduser().resolve(), "r") as f:
                    user_request = f.read()

        result = await agent.step(user_request)

        print(result)
        print()


if __name__ == "__main__":
    asyncio.run(main())
