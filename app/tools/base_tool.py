from abc import ABC, abstractmethod


class ToolError(Exception):
    """Raise for expected, recoverable tool failures. The message goes back to the LLM."""


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    input_schema: dict = {"type": "object", "properties": {}}

    @abstractmethod
    def run(self, **kwargs) -> str:
        """Execute the tool and return a string observation."""

    def to_schema(self) -> dict:
        """Tool definition in the format the Anthropic API expects."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }