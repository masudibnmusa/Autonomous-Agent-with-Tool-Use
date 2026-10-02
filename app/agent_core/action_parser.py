"""Turn raw LLM responses into tool name + args.

With native tool calling the API already returns structured blocks, so this
mostly normalizes them. `parse_text_action` is a fallback for text-based ReAct.
"""
import json
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class ParsedResponse:
    thought: str                                   # text the model wrote (reasoning or final answer)
    tool_calls: List[ToolCall] = field(default_factory=list)
    assistant_content: list = field(default_factory=list)  # plain dicts, safe to send back

    @property
    def is_final(self) -> bool:
        return not self.tool_calls


def parse_response(response) -> ParsedResponse:
    texts, calls, content = [], [], []
    for block in response.content:
        block_type = getattr(block, "type", None)
        if block_type == "text":
            if block.text.strip():
                texts.append(block.text)
                content.append({"type": "text", "text": block.text})
        elif block_type == "tool_use":
            args = dict(block.input or {})
            calls.append(ToolCall(block.id, block.name, args))
            content.append({"type": "tool_use", "id": block.id, "name": block.name, "input": args})
    return ParsedResponse("\n".join(texts).strip(), calls, content)


def parse_text_action(text: str) -> Optional[dict]:
    """Fallback: extract {"tool": "...", "args": {...}} from free text. Returns None if absent."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and "tool" in data and isinstance(data.get("args", {}), dict):
        return {"tool": data["tool"], "args": data.get("args", {})}
    return None