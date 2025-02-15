import re
from openai import OpenAI

client = OpenAI(
    api_key="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"
)

system_prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

Example session:

Question: What is 2 + 3?
Thought: I need calculate
Action: calculate: 2 + 3
PAUSE 

You will be called again with this:

Observation: 5

If you have the answer, output it as the Answer.

Answer: The result is 5

Now it's your turn:
""".strip()


def calculate(operation: str) -> float:
    return eval(operation)

class Agent:
    def __init__(self, client: OpenAI, system: str = "") -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = client.chat.completions.create(
            model="gpt-4o", messages=self.messages
        )
        print("-----")
        print(completion.choices[0])
        print("-----")
        return completion.choices[0].message.content

def loop(max_iterations=10, query: str = ""):
    agent = Agent(client=client, system=system_prompt)

    tools = ["calculate"]

    next_prompt = query

    i = 0

    while i < max_iterations:
        i += 1
        result = agent(next_prompt)
        print(result)

        if "PAUSE" in result and "Action" in result:
            action = re.findall(r"Action: ([a-z_]+): (.+)", result, re.IGNORECASE)
            chosen_tool = action[0][0]
            arg = action[0][1]

            if chosen_tool in tools:
                result_tool = eval(f"{chosen_tool}('{arg}')")
                next_prompt = f"Observation: {result_tool}"

            else:
                next_prompt = "Observation: Tool not found"

            print(next_prompt)
            continue

        if "Answer" in result:
            break


loop(query="How much is 55 + 1?")
