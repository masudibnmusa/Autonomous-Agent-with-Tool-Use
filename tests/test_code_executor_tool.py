from app.sandbox.code_sandbox import CodeSandbox
from app.tools.code_executor_tool import CodeExecutorTool


def make_tool():
    # Subprocess mode so tests don't need Docker
    return CodeExecutorTool(CodeSandbox(mode="subprocess", timeout=3, memory_mb=512))


def test_runs_code_and_captures_stdout():
    output = make_tool().run("print(2 + 2)")
    assert "4" in output
    assert "Exit code: 0" in output


def test_reports_errors():
    output = make_tool().run("raise ValueError('boom')")
    assert "ValueError" in output
    assert "Exit code: 0" not in output


def test_times_out():
    output = make_tool().run("while True: pass")
    assert "timed out" in output.lower()