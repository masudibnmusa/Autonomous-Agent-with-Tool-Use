# Autonomous Agent with Tool Use

An LLM-powered agent that plans and executes multi-step tasks on its own. It can browse the web, run code in a sandbox, call APIs, and do math, deciding at each step which tool to use, observing the result, and continuing until the task is done.

Built on the **ReAct (Reason + Act)** pattern: the model alternates between reasoning about what to do and taking an action, instead of producing a single static response.

---

## Features

- **ReAct loop**: think, act, observe, repeat until the task is complete
- **Pluggable tools**: web search, URL browsing, sandboxed Python execution, REST API calls, calculator, scratch-file access
- **Tool registry**: add a new tool by implementing one small interface
- **Sandboxed code execution**: Docker or subprocess isolation with timeout and memory limits
- **Safety guardrails**: action validation, allowlisted APIs, human approval for sensitive actions
- **Stopping conditions**: max iterations, explicit completion signal, error threshold
- **Context management**: trims or summarizes history as it grows
- **Full trace logging**: every thought, action, and observation saved for debugging and transparency
- **Multiple interfaces**: CLI and Streamlit

---

## How It Works

1. **Task input**: you give the agent a goal, e.g. *"Find the top 5 Python web frameworks by GitHub stars and summarize their pros and cons."*
2. **Planning** (optional): the LLM breaks the goal into a rough plan, either upfront or step by step.
3. **Tool selection**: on each step the LLM outputs a thought, a chosen tool, and the tool input in a structured format.
4. **Tool execution**: the system runs the tool (search API, Python sandbox, REST call) and captures the result.
5. **Observation**: the output is appended to the agent's context.
6. **Loop**: the LLM reasons over the new context and either calls another tool or gives a final answer.
7. **Stop**: the loop ends on a completion signal, the iteration limit, or the error threshold.
8. **Output**: a compiled answer plus a trace of everything the agent did.

```
User goal
     |
     v
planner.py (optional upfront plan)
     |
     v
+--------------- agent_loop.py (repeats) ---------------+
|  LLM reasons -> chooses tool + input                  |
|       |                                               |
|       v                                               |
|  action_parser.py -> registry.py (dispatch to tool)   |
|       |                                               |
|       v                                               |
|  tools/*.py executes -> result captured               |
|       |                                               |
|       v                                               |
|  scratchpad.py (append thought + action + observation)|
|       |                                               |
|       v                                               |
|  stopping_criteria.py -> done? loop again? fail?      |
+-------------------------------------------------------+
     |
     v
Final answer + trace_logger.py (full run log)
```

---

## Project Structure

```
autonomous-agent/
├── app/
│   ├── main.py                  # Entry point (CLI / Streamlit)
│   ├── config.py                # API keys, max iterations, allowed tools
│   │
│   ├── agent_core/
│   │   ├── agent_loop.py        # Main ReAct loop
│   │   ├── planner.py           # Optional upfront task decomposition
│   │   ├── action_parser.py     # Parse LLM output into tool name + args
│   │   └── stopping_criteria.py # Max steps, completion detection, error limits
│   │
│   ├── tools/
│   │   ├── base_tool.py         # Abstract tool interface
│   │   ├── registry.py          # Registers and exposes tools to the LLM
│   │   ├── web_search_tool.py   # Web search (SerpAPI / Tavily / Bing)
│   │   ├── web_browse_tool.py   # Fetch + parse a URL
│   │   ├── code_executor_tool.py# Run Python in a sandbox
│   │   ├── api_caller_tool.py   # Generic REST API wrapper
│   │   ├── calculator_tool.py   # Arithmetic
│   │   └── file_tool.py         # Read/write files in a scratch workspace
│   │
│   ├── sandbox/
│   │   ├── code_sandbox.py      # Isolated execution (Docker / subprocess)
│   │   └── resource_limiter.py  # Timeout, memory limits, network control
│   │
│   ├── memory/
│   │   ├── scratchpad.py        # Running log of thoughts/actions/observations
│   │   └── context_manager.py   # Trim/summarize context as it grows
│   │
│   ├── llm/
│   │   ├── llm_client.py        # Claude/GPT API wrapper (tool calling)
│   │   └── prompt_templates.py  # System prompt defining tool-use rules
│   │
│   ├── safety/
│   │   ├── action_validator.py  # Block disallowed or risky actions
│   │   └── human_approval.py    # Ask user to confirm sensitive actions
│   │
│   └── utils/
│       └── trace_logger.py      # Log full agent trajectory
│
├── data/
│   ├── traces/                  # Saved run logs
│   └── workspace/               # Scratch files the agent reads/writes
│
├── tests/
├── .env.example
├── requirements.txt
├── Dockerfile                   # Sandbox image for code execution
├── run.sh
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Docker (recommended, for sandboxed code execution)
- An LLM API key (Anthropic or OpenAI)
- A search API key (SerpAPI, Tavily, or Bing)

### Installation

```bash
git clone https://github.com/masudibnmusa/Autonomous-Agent-with-Tool-Use.git
cd autonomous-agent

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Environment Setup

```bash
cp .env.example .env
```

Then edit `.env`:

```env
ANTHROPIC_API_KEY=your_key_here
# or
OPENAI_API_KEY=your_key_here

SEARCH_API_KEY=your_search_key_here
MAX_ITERATIONS=15
```

### Build the Sandbox Image

```bash
docker build -t agent-sandbox .
```

---

## Usage

### CLI

```bash
python -m app.main --goal "Find the top 5 Python web frameworks by GitHub stars and summarize their pros and cons"
```

Or use the helper script:

```bash
./run.sh "Your task here"
```

### Streamlit

```bash
streamlit run app/main.py
```

### Example Output

```
[Step 1] Thought: I need current GitHub star counts for Python web frameworks.
         Action:  web_search("most popular Python web frameworks GitHub stars")
[Step 2] Thought: I have candidates. I'll check each repo's star count.
         Action:  api_caller(GET https://api.github.com/repos/django/django)
...
[Step 9] Thought: I have everything I need.
         Final Answer: <summary with pros/cons>

Trace saved to data/traces/run_2025-01-01_12-00-00.json
```

---

## Configuration

Settings live in `app/config.py` and can be overridden via `.env`.

| Setting | Description | Default |
|---|---|---|
| `MAX_ITERATIONS` | Hard cap on loop steps | `15` |
| `MAX_CONSECUTIVE_ERRORS` | Stop after this many tool failures in a row | `3` |
| `ALLOWED_TOOLS` | Tools exposed to the LLM | all |
| `ALLOWED_API_DOMAINS` | Allowlist for `api_caller_tool` | `[]` |
| `SANDBOX_TIMEOUT_SEC` | Max runtime for executed code | `10` |
| `SANDBOX_MEMORY_MB` | Memory cap for executed code | `256` |
| `REQUIRE_APPROVAL` | Ask the user before risky actions | `true` |
| `MODEL_NAME` | LLM used for reasoning | configurable |

---

## Available Tools

| Tool | Purpose |
|---|---|
| `web_search` | Search the web and return top results |
| `web_browse` | Fetch and parse the content of a specific URL |
| `code_executor` | Run Python in an isolated sandbox |
| `api_caller` | Make REST calls to allowlisted domains |
| `calculator` | Exact arithmetic (LLMs are unreliable at math) |
| `file_tool` | Read/write files in `data/workspace/` only |

---

## Safety

Agents act on their own, so safety is built in rather than bolted on.

- **Sandboxed execution**: code runs in a container with no network by default, CPU/memory caps, timeouts, and a restricted filesystem.
- **Action validation**: `action_validator.py` blocks disallowed tools, domains, and file paths before anything runs.
- **Human-in-the-loop**: sensitive actions pause for explicit user approval.
- **Allowlisted APIs**: the agent can only call domains you approve.
- **Untrusted content handling**: web pages and tool outputs are treated as **data, not instructions**, to reduce prompt-injection risk.
- **Hard stops**: iteration and error limits prevent runaway loops.

> **Note:** No sandbox is perfect. Do not run this agent with credentials or data you can't afford to expose.

---

## Testing

```bash
pytest tests/
```

| Test file | Covers |
|---|---|
| `test_agent_loop.py` | Loop control flow and tool dispatch |
| `test_action_parser.py` | Parsing valid and malformed LLM output |
| `test_web_search_tool.py` | Search tool behavior (mocked) |
| `test_code_executor_tool.py` | Sandbox execution, timeouts, limits |
| `test_stopping_criteria.py` | Max steps, completion, error thresholds |

---

## Adding a New Tool

1. Create `app/tools/my_tool.py` and subclass `BaseTool`:

```python
from app.tools.base_tool import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "One clear sentence on what this tool does and when to use it."

    def run(self, **kwargs) -> str:
        # do the work, return a string observation
        return "result"
```

2. Register it in `app/tools/registry.py`.
3. Add it to `ALLOWED_TOOLS` in `config.py`.
4. Add a test in `tests/`.

Clear tool descriptions matter: they're what the LLM uses to decide when to call your tool.

## License

MIT.