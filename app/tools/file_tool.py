"""Read/write files, restricted to the scratch workspace."""
from pathlib import Path

from app import config
from app.tools.base_tool import BaseTool, ToolError

MAX_WRITE_BYTES = 1_000_000


class FileTool(BaseTool):
    name = "file_tool"
    description = (
        "Read, write, or list files in the agent's scratch workspace. "
        "Paths are relative to the workspace; nothing outside it is accessible."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["read", "write", "list"]},
            "path": {"type": "string", "description": "Relative path (ignored for 'list' of root)", "default": "."},
            "content": {"type": "string", "description": "Content to write (for 'write')"},
        },
        "required": ["action"],
    }

    def __init__(self, workspace: Path = None):
        self.root = Path(workspace or config.WORKSPACE_DIR).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root):
            raise ToolError("Path escapes the workspace.")
        return target

    def run(self, action: str, path: str = ".", content: str = None) -> str:
        target = self._resolve(path)
        if action == "list":
            if not target.exists():
                raise ToolError("Directory does not exist.")
            items = sorted(p.name + ("/" if p.is_dir() else "") for p in target.iterdir())
            return "\n".join(items) or "(empty)"
        if action == "read":
            if not target.is_file():
                raise ToolError("File not found.")
            return target.read_text(errors="replace")
        if action == "write":
            if content is None:
                raise ToolError("'content' is required for write.")
            if len(content.encode()) > MAX_WRITE_BYTES:
                raise ToolError("Content too large.")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
            return f"Wrote {len(content)} characters to {path}"
        raise ToolError(f"Unknown action '{action}'.")