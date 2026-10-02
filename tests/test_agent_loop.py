from types import SimpleNamespace as NS

from app.agent_core.agent_loop import Agent
from app.agent_core.stopping_criteria import StoppingCriteria
from app.memory.context_manager import ContextManager
from app.safety.action_validator import ActionValidator
from app.safety.human_approval import HumanApproval
from app.tools.calculator_tool import CalculatorTool
from app.tools.registry import ToolRegistry
from app.utils.trace_logger import TraceLogger


class FakeLLM:
    model = "fake"

    def __init__(self, responses):
        self.responses = list(responses)

    def chat(self, system, messages, tools=None, **kwargs):
        return self.responses.pop(0)


def text(t):
    return NS(content=[NS(type="text", text=t)])


def tool_use(name, args, id="t1"):
    return NS(content=[NS(type="tool_use", id=id, name=name, input=args)])


def make_agent(responses, tmp_path, max_iterations=5):
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    return Agent(
        llm=FakeLLM(responses),
        registry=registry,
        validator=ActionValidator(registry.names()),
        approver=HumanApproval(auto_approve=True),
        criteria=StoppingCriteria(max_iterations, 3),
        context_manager=ContextManager(),
        logger=TraceLogger(tmp_path),
    )


def test_completes_after_tool_use(tmp_path):
    agent = make_agent(
        [tool_use("calculator", {"expression": "6*7"}), text("The answer is 42.")], tmp_path
    )
    result = agent.run("What is 6*7?")
    assert result.stop_reason == "completed"
    assert "42" in result.answer
    assert result.steps == 2


def test_stops_at_max_iterations(tmp_path):
    agent = make_agent(
        [
            tool_use("calculator", {"expression": "1+1"}, "a"),
            tool_use("calculator", {"expression": "2+2"}, "b"),
            text("Best effort answer."),  # wrap-up call
        ],
        tmp_path,
        max_iterations=2,
    )
    result = agent.run("loop forever")
    assert result.stop_reason == "max_iterations"
    assert result.answer == "Best effort answer."


def test_unknown_tool_is_reported_as_error(tmp_path):
    agent = make_agent([tool_use("hack_the_planet", {}), text("Gave up.")], tmp_path)
    result = agent.run("do something")
    assert result.stop_reason == "completed"
    assert result.trace_path