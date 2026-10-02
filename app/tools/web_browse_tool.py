"""Fetch a URL and return readable text. Blocks private/internal addresses (SSRF protection)."""
import ipaddress
import socket
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.tools.base_tool import BaseTool, ToolError

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AutonomousAgent/1.0)"}
MAX_REDIRECTS = 3


def is_public_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        return False
    for info in infos:
        ip = ipaddress.ip_address(info[4][0].split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


class WebBrowseTool(BaseTool):
    name = "web_browse"
    description = (
        "Fetch a web page by URL and return its readable text content. "
        "Only public http(s) URLs are allowed."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "Full URL starting with http:// or https://"},
            "max_chars": {"type": "integer", "description": "Max characters to return", "default": 5000},
        },
        "required": ["url"],
    }

    def run(self, url: str, max_chars: int = 5000) -> str:
        max_chars = max(500, min(int(max_chars), 12000))
        current = url
        for _ in range(MAX_REDIRECTS + 1):
            if not is_public_url(current):
                raise ToolError(f"Blocked or invalid URL: {current}")
            try:
                resp = requests.get(current, headers=HEADERS, timeout=15, allow_redirects=False)
            except requests.RequestException as e:
                raise ToolError(f"Request failed: {e}")
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location")
                if not location:
                    raise ToolError("Redirect without Location header.")
                current = urljoin(current, location)
                continue
            break
        else:
            raise ToolError("Too many redirects.")

        if resp.status_code >= 400:
            raise ToolError(f"HTTP {resp.status_code} for {current}")

        content_type = resp.headers.get("Content-Type", "")
        if "html" in content_type:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
                tag.decompose()
            text = soup.get_text("\n", strip=True)
        elif "text" in content_type or "json" in content_type:
            text = resp.text
        else:
            raise ToolError(f"Unsupported content type: {content_type}")

        return f"URL: {current}\n\n{text[:max_chars]}"