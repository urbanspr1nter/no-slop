from orchestrator.agent import Agent
from config.loader import load_config, Config

if __name__ == "__main__":
    config: Config = load_config()
    agent = Agent(config=config)

    agent.set_system_prompt("You are a helpful assistant. Keep your responses concise.")

    while True:
        user_request = input("? ")

        if user_request == "/bye":
            break

        result = agent.step(user_request)

        print(result)
        print()
