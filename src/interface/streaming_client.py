import os
import argparse
import datetime
from pathlib import Path
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from orchestrator.streaming_agent import StreamingAgent
from config.loader import load_config, Config
from utils.path_utils import make_real_path
from utils.noslop_dir_utils import create_noslop_path_idem
from config.updater import update_config_file

import asyncio

history = InMemoryHistory()

NO_SLOP_DIRECTORY = ".noslop"


def init():
    create_noslop_path_idem()


async def main():
    init()

    config: Config = load_config()

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--system-prompt")
    parser.add_argument("-w", "--workspace")
    parser.add_argument("--session-resume")
    parser.add_argument("-p", "--prompt")
    parser.add_argument("-t")

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

    if args.session_resume:
        print(f"Resuming session: {args.session_resume}")

    system_prompt = system_prompt.replace("{{workspace_dir}}", config.workspace, 1)
    system_prompt = system_prompt.replace(
        "{{current_date}}", datetime.datetime.today().strftime("%Y-%m-%d")
    )

    agent = StreamingAgent(config=config, session_id=args.session_resume)
    agent.set_system_prompt(system_prompt)

    if args.prompt:
        user_request = args.prompt.strip()
        if not user_request:
            return

        await agent.step(user_request, headless=True)
    else:
        print(f"<system_prompt>\n{system_prompt}\n</system_prompt>")

        for m in agent.get_context():
            if m.get("type", None) == "message":
                if m["role"] == "user":
                    print(f"[user]: {m["content"][0]["text"].strip()}")
                elif m["role"] == "assistant":
                    print(f"[assistant]: {m["content"][0]["text"].strip()}")
            elif m.get("type", None) == "function_call":
                print(m)
            elif m.get("type", None) == "function_call_output":
                print(m)
            else:
                if m.get("role", None) == "system":
                    print(f"<system_prompt>\n{m["content"]}\n</system_prompt>")
                else:
                    print(m)
            print()

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
            elif user_request.startswith("/config"):
                # Ex: /config providers.local.model qwen3.6-9b
                config_request_parts = user_request.split()
                config_key = config_request_parts[1]
                config_value = config_request_parts[2]

                update_config_file(config_key, config_value)

                continue
            elif user_request.startswith("/prompt"):
                filepath = user_request.split(" ")[-1]
                if os.path.exists(Path(filepath).expanduser().resolve()):
                    with open(Path(filepath).expanduser().resolve(), "r") as f:
                        user_request = f.read()
            elif user_request.startswith("/save"):
                agent.save_session()
                continue

            await agent.step(user_request)

            # Save session after agent response
            agent.save_session()


if __name__ == "__main__":
    asyncio.run(main())
