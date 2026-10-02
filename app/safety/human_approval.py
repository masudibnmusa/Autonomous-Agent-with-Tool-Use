import json
from typing import Callable, Optional


class HumanApproval:
    """Pause for confirmation on sensitive actions.

    - auto_approve=True: always approve (use only for testing)
    - callback: custom decision function (used by the Streamlit UI)
    - default: ask on the terminal
    """

    def __init__(self, callback: Optional[Callable] = None, auto_approve: bool = False):
        self.callback = callback
        self.auto_approve = auto_approve

    def request(self, tool: str, args: dict, reason: str) -> bool:
        if self.auto_approve:
            return True
        if self.callback:
            return bool(self.callback(tool, args, reason))
        print(f"\n[Approval needed] {reason}")
        print(f"  Tool: {tool}")
        print(f"  Args: {json.dumps(args)[:500]}")
        try:
            return input("  Approve? [y/N]: ").strip().lower() in ("y", "yes")
        except EOFError:
            return False