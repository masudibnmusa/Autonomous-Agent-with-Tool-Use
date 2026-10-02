from typing import Dict, List, Optional

from app import config
from app.tools.base_tool import BaseTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def names(self) -> List[str]:
        return list(self._tools)

    def schemas(self) -> List[dict]:
        return [t.to_schema() for t in self._tools.values()]

    def describe(self) -> str:
        return "\n".join(f"- {t.name}: {t.description}" for t in self._tools.values())


def build_default_registry(allowed: Optional[List[str]] = None) -> ToolRegistry:
    from app.tools.api_caller_tool import ApiCallerTool
    from app.tools.calculator_tool import CalculatorTool
    from app.tools.code_executor_tool import CodeExecutorTool
    from app.tools.file_tool import FileTool
    from app.tools.web_browse_tool import WebBrowseTool
    from app.tools.web_search_tool import WebSearchTool

    allowed = config.ALLOWED_TOOLS if allowed is None else allowed
    registry = ToolRegistry()
    for tool in [
        WebSearchTool(),
        WebBrowseTool(),
        CodeExecutorTool(),
        ApiCallerTool(),
        CalculatorTool(),
        FileTool(),
    ]:
        if tool.name in allowed:
            registry.register(tool)
    return registry