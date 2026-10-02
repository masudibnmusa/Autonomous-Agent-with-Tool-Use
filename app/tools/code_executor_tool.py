from app.sandbox.code_sandbox import CodeSandbox
from app.tools.base_tool import BaseTool


class CodeExecutorTool(BaseTool):
    name = "code_executor"
    description = (
        "Run Python 3 code in an isolated sandbox with no network access. "
        "Use print() to output results. State is NOT kept between calls, so include all "
        "needed code each time. numpy and pandas are available."
    )
    input_schema = {
        "type": "object",
        "properties": {"code": {"type": "string", "description": "Python code to execute"}},
        "required": ["code"],
    }

    def __init__(self, sandbox: CodeSandbox = None):
        self.sandbox = sandbox or CodeSandbox()

    def run(self, code: str) -> str:
        return self.sandbox.run_python(code).format()