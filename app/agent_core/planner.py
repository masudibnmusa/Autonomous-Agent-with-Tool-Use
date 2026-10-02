"""Optional upfront task decomposition."""
from app.llm.prompt_templates import PLANNER_PROMPT


class Planner:
    def __init__(self, llm):
        self.llm = llm

    def make_plan(self, goal: str, tool_descriptions: str) -> str:
        response = self.llm.chat(
            PLANNER_PROMPT.format(tools=tool_descriptions),
            [{"role": "user", "content": goal}],
            max_tokens=600,
        )
        return "".join(b.text for b in response.content if b.type == "text").strip()