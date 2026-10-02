"""Central configuration. Values come from environment / .env."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TRACE_DIR = DATA_DIR / "traces"
WORKSPACE_DIR = DATA_DIR / "workspace"
TRACE_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def _list(name: str, default: str = "") -> list:
    raw = os.getenv(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# LLM
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "claude-sonnet-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

# Search
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")

# Agent loop
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "15"))
MAX_CONSECUTIVE_ERRORS = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "3"))
USE_PLANNER = _bool("USE_PLANNER", "false")

# Tools
ALLOWED_TOOLS = _list(
    "ALLOWED_TOOLS",
    "web_search,web_browse,code_executor,api_caller,calculator,file_tool",
)
ALLOWED_API_DOMAINS = _list("ALLOWED_API_DOMAINS", "api.github.com")
MAX_OBSERVATION_CHARS = int(os.getenv("MAX_OBSERVATION_CHARS", "6000"))

# Sandbox
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "docker")  # "docker" or "subprocess"
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "agent-sandbox")
SANDBOX_TIMEOUT_SEC = int(os.getenv("SANDBOX_TIMEOUT_SEC", "10"))
SANDBOX_MEMORY_MB = int(os.getenv("SANDBOX_MEMORY_MB", "256"))

# Safety
REQUIRE_APPROVAL = _bool("REQUIRE_APPROVAL", "true")

# Context
CONTEXT_KEEP_LAST = int(os.getenv("CONTEXT_KEEP_LAST", "6"))