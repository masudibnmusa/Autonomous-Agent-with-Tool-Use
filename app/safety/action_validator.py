"""Decide whether a requested action is allowed, needs approval, or is blocked."""
from dataclasses import dataclass
from typing import List

# Heuristic only. The real protection is the sandbox, not this list.
SUSPICIOUS_CODE_PATTERNS = [
    "os.system", "subprocess", "shutil.rmtree", "socket", "__import__", "eval(", "exec(",
]


@dataclass
class Verdict:
    allowed: bool
    needs_approval: bool = False
    reason: str = ""


class ActionValidator:
    def __init__(self, allowed_tools: List[str], require_approval: bool = True):
        self.allowed_tools = set(allowed_tools)
        self.require_approval = require_approval

    def validate(self, name: str, args: dict) -> Verdict:
        if name not in self.allowed_tools:
            return Verdict(False, reason=f"Tool '{name}' is not allowed.")
        if not isinstance(args, dict):
            return Verdict(False, reason="Tool arguments must be an object.")

        if name == "api_caller":
            method = str(args.get("method", "GET")).upper()
            if method != "GET":
                return Verdict(True, self.require_approval, f"State-changing API request ({method}).")

        if name == "code_executor":
            code = str(args.get("code", ""))
            hits = [p for p in SUSPICIOUS_CODE_PATTERNS if p in code]
            if hits:
                return Verdict(True, self.require_approval, f"Code uses risky constructs: {', '.join(hits)}.")

        return Verdict(True)


def wrap_untrusted(tool_name: str, text: str) -> str:
    """Mark tool output as data. Neutralize any attempt to close the tag early."""
    safe = text.replace("</tool_output>", "[/tool_output]")
    return f'<tool_output tool="{tool_name}">\n{safe}\n</tool_output>'