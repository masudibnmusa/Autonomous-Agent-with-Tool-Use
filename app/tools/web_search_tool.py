"""Web search via Tavily. To use SerpAPI or Bing, change only the request/response handling below."""
import requests

from app import config
from app.tools.base_tool import BaseTool, ToolError


class WebSearchTool(BaseTool):
    name = "web_search"
    description = (
        "Search the web for current information. Returns titles, URLs, and short snippets. "
        "Use web_browse afterwards to read a specific page in full."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Number of results (1-8)", "default": 5},
        },
        "required": ["query"],
    }

    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.SEARCH_API_KEY

    def run(self, query: str, max_results: int = 5) -> str:
        if not self.api_key:
            raise ToolError("SEARCH_API_KEY is not configured.")
        max_results = max(1, min(int(max_results), 8))
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": self.api_key, "query": query, "max_results": max_results},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ToolError(f"Search request failed: {e}")

        results = resp.json().get("results", [])
        if not results:
            return "No results found."
        lines = []
        for i, r in enumerate(results, 1):
            snippet = (r.get("content") or "")[:500]
            lines.append(f"{i}. {r.get('title', 'Untitled')}\n   {r.get('url', '')}\n   {snippet}")
        return "\n\n".join(lines)