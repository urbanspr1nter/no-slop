import os
import argparse
import platform
import json
import datetime
from pathlib import Path

from orchestrator.streaming_agent import StreamingAgent
from config.loader import load_config, Config
from utils.path_utils import make_real_path
from utils.noslop_dir_utils import create_noslop_path_idem

import asyncio

NO_SLOP_DIRECTORY = ".noslop"


def init():
    create_noslop_path_idem()


def get_platform_information():
    result = {
        "machine_arch": platform.machine(),
        "platform": platform.platform(),
    }
    if platform.freedesktop_os_release():
        info = dict(platform.freedesktop_os_release())

        result = {
            **result,
            "distribution_name": info["NAME"],
            "version": info["VERSION"],
        }

    return result


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
    system_prompt = system_prompt.replace(
        "{{operating_system}}", json.dumps(get_platform_information(), indent=2)
    )
    system_prompt = system_prompt.replace(
        "{{max_tool_call_output_length}}", str(config.max_tool_call_output_length)
    )

    agent = StreamingAgent(config=config, session_id=args.session_resume)
    agent.set_system_prompt(system_prompt)

    if args.prompt:
        user_request = f"""You are in headless mode. Fulfill the following:

{args.prompt.strip()}"""

        await agent.step(user_request, headless=True)
    else:
        # curses TUI: handles the prompt loop, streaming display, and the
        # /bye, /config, /prompt, /save commands
        from interface.curses_tui import CursesTUI

        tui = CursesTUI(
            agent=agent, model_id=config.model_id, workspace=config.workspace
        )
        tui.run()


if __name__ == "__main__":
    asyncio.run(main())
