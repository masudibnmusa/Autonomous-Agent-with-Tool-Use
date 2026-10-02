import pytest

from app.tools import web_search_tool
from app.tools.base_tool import ToolError
from app.tools.web_search_tool import WebSearchTool


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"results": [{"title": "Flask", "url": "https://flask.palletsprojects.com", "content": "A micro framework"}]}


def test_formats_results(monkeypatch):
    monkeypatch.setattr(web_search_tool.requests, "post", lambda *a, **k: FakeResponse())
    output = WebSearchTool(api_key="test").run("python frameworks")
    assert "Flask" in output
    assert "https://flask.palletsprojects.com" in output


def test_requires_api_key():
    with pytest.raises(ToolError):
        WebSearchTool(api_key="").run("anything")