"""Running log of thoughts / actions / observations (used for the trace)."""
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Step:
    index: int
    thought: str
    tool: str
    args: dict
    observation: str
    is_error: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Scratchpad:
    def __init__(self):
        self.plan: Optional[str] = None
        self.steps: List[Step] = []
        self.final_answer: Optional[str] = None

    def add(self, index, thought, tool, args, observation, is_error) -> None:
        self.steps.append(Step(index, thought, tool, args, observation, is_error))

    def to_dict(self) -> dict:
        return {
            "plan": self.plan,
            "steps": [asdict(s) for s in self.steps],
            "final_answer": self.final_answer,
        }