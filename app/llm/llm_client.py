"""Thin wrapper around the Anthropic Messages API (native tool calling)."""
import anthropic

from app import config


class LLMClient:
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model or config.MODEL_NAME
        # The SDK already retries transient errors; we just raise the retry count.
        self.client = anthropic.Anthropic(api_key=api_key or config.ANTHROPIC_API_KEY, max_retries=3)

    def chat(self, system: str, messages: list, tools: list = None,
             max_tokens: int = None, tool_choice: dict = None):
        kwargs = dict(
            model=self.model,
            max_tokens=max_tokens or config.MAX_TOKENS,
            system=system,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        return self.client.messages.create(**kwargs)