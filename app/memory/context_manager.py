"""Keep the context from growing without bound.

Strategy: always keep the first message (the goal) and the last N messages intact;
shrink tool outputs in older messages. Message structure is preserved so
tool_use / tool_result pairs stay valid. (Upgrade idea: summarize old steps with the LLM.)
"""


class ContextManager:
    def __init__(self, keep_last: int = 6, max_old_chars: int = 300):
        self.keep_last = keep_last
        self.max_old_chars = max_old_chars

    def trim(self, messages: list) -> list:
        if len(messages) <= self.keep_last + 1:
            return messages
        cutoff = len(messages) - self.keep_last
        trimmed = []
        for i, message in enumerate(messages):
            if i == 0 or i >= cutoff:
                trimmed.append(message)
            else:
                trimmed.append(self._shrink(message))
        return trimmed

    def _shrink(self, message: dict) -> dict:
        if message["role"] != "user" or not isinstance(message["content"], list):
            return message
        blocks = []
        for block in message["content"]:
            content = block.get("content")
            if block.get("type") == "tool_result" and isinstance(content, str) and len(content) > self.max_old_chars:
                block = {**block, "content": content[: self.max_old_chars] + " ...[older output truncated]"}
            blocks.append(block)
        return {**message, "content": blocks}