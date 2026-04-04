from orchestrator.agent import Agent

if __name__ == "__main__":
    agent = Agent()

    agent.set_system_prompt("You are a helpful assistant. Keep your responses concise.")

    while True:
        user_request = input("? ")

        if user_request == "/bye":
            break

        result = agent.step(user_request)

        print(result)
        print()
