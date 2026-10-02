"""Generic REST client restricted to an allowlist of domains."""
from urllib.parse import urlparse

import requests

from app import config
from app.tools.base_tool import BaseTool, ToolError


class ApiCallerTool(BaseTool):
    name = "api_caller"
    description = (
        "Make an HTTPS REST API call to an allowlisted domain and return the status and body. "
        "Non-GET methods require user approval."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "url": {"type": "string", "description": "Full https URL"},
            "headers": {"type": "object", "description": "Optional request headers"},
            "json_body": {"type": "object", "description": "Optional JSON body"},
        },
        "required": ["method", "url"],
    }

    def __init__(self, allowed_domains: list = None):
        self.allowed_domains = allowed_domains if allowed_domains is not None else config.ALLOWED_API_DOMAINS

    def run(self, method: str, url: str, headers: dict = None, json_body: dict = None) -> str:
        method = method.upper()
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ToolError("Only https URLs are allowed.")
        if parsed.hostname not in self.allowed_domains:
            raise ToolError(
                f"Domain '{parsed.hostname}' is not allowlisted. Allowed: {self.allowed_domains}"
            )
        try:
            resp = requests.request(
                method,
                url,
                headers={"User-Agent": "AutonomousAgent/1.0", **(headers or {})},
                json=json_body,
                timeout=15,
                allow_redirects=False,  # a redirect could leave the allowlist
            )
        except requests.RequestException as e:
            raise ToolError(f"Request failed: {e}")
        return f"HTTP {resp.status_code}\n{resp.text[:5000]}"