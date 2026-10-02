"""Main ReAct loop: think -> act -> observe -> repeat."""
from dataclasses import dataclass
from typing import Callable, Optional

from app import config
from app.agent_core.action_parser import ToolCall, parse_response
from app.llm.prompt_templates import SYSTEM_PROMPT
from app.memory.scratchpad import Scratchpad
from app.safety.action_validator import wrap_untrusted


@dataclass
class AgentResult:
    answer: str
    stop_reason: str
    steps: int
    trace_path: Optional[str]


class Agent:
    def __init__(
        self,
        llm,
        registry,
        validator,
        approver,
        criteria,
        context_manager,
        logger,
        planner=None,
        on_event: Optional[Callable[[dict], None]] = None,
    ):
        self.llm = llm
        self.registry = registry
        self.validator = validator
        self.approver = approver
        self.criteria = criteria
        self.context = context_manager
        self.logger = logger
        self.planner = planner
        self.on_event = on_event

    def _emit(self, **event) -> None:
        if self.on_event:
            self.on_event(event)

    def run(self, goal: str) -> AgentResult:
        pad = Scratchpad()
        first_message = goal

        if self.planner:
            plan = self.planner.make_plan(goal, self.registry.describe())
            pad.plan = plan
            self._emit(type="plan", plan=plan)
            first_message = f"{goal}\n\nSuggested plan (adapt it as you learn more):\n{plan}"

        messages = [{"role": "user", "content": first_message}]
        tools = self.registry.schemas()
        consecutive_errors = 0
        stop_reason = "completed"
        answer = ""
        step = 0

        while True:
            step += 1
            response = self.llm.chat(SYSTEM_PROMPT, self.context.trim(messages), tools)
            parsed = parse_response(response)

            # No tool calls -> the model is giving its final answer
            if parsed.is_final:
                answer = parsed.thought
                break

            messages.append({"role": "assistant", "content": parsed.assistant_content})

            results = []
            for call in parsed.tool_calls:
                observation, is_error = self._execute(call)
                pad.add(step, parsed.thought, call.name, call.args, observation, is_error)
                self._emit(
                    type="step",
                    index=step,
                    thought=parsed.thought,
                    tool=call.name,
                    args=call.args,
                    observation=observation,
                    is_error=is_error,
                )
                consecutive_errors = consecutive_errors + 1 if is_error else 0
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": call.id,
                        "content": wrap_untrusted(call.name, observation),
                        "is_error": is_error,
                    }
                )
            messages.append({"role": "user", "content": results})

            reason = self.criteria.check(step, consecutive_errors)
            if reason:
                stop_reason = reason
                answer = self._wrap_up(messages, reason)
                break

        pad.final_answer = answer
        self._emit(type="final", answer=answer, stop_reason=stop_reason)
        trace_path = self.logger.save(
            goal, pad, answer, stop_reason, getattr(self.llm, "model", "")
        )
        return AgentResult(answer, stop_reason, step, trace_path)

    def _execute(self, call: ToolCall):
        """Validate -> (approve) -> run. Returns (observation, is_error)."""
        verdict = self.validator.validate(call.name, call.args)
        if not verdict.allowed:
            return f"BLOCKED: {verdict.reason}", True

        if verdict.needs_approval and not self.approver.request(
            call.name, call.args, verdict.reason
        ):
            return "DENIED: the user did not approve this action.", True

        tool = self.registry.get(call.name)
        if tool is None:
            return (
                f"Unknown tool '{call.name}'. Available tools: {', '.join(self.registry.names())}",
                True,
            )
        try:
            output = str(tool.run(**call.args))
            if len(output) > config.MAX_OBSERVATION_CHARS:
                output = output[: config.MAX_OBSERVATION_CHARS] + "\n...[output truncated]"
            return output, False
        except TypeError as e:
            return f"Invalid arguments for {call.name}: {e}", True
        except Exception as e:  # ToolError and anything unexpected
            return f"Tool error: {type(e).__name__}: {e}", True

    def _wrap_up(self, messages: list, reason: str) -> str:
        """Ask for a best-effort final answer when a stopping limit is hit."""
        note = {
            "type": "text",
            "text": (
                f"Stopping condition reached ({reason}). Do not call any more tools. "
                "Write the best final answer you can from what you have gathered, "
                "and clearly say what is incomplete."
            ),
        }
        last = messages[-1]
        wrapped = messages[:-1] + [{"role": "user", "content": list(last["content"]) + [note]}]
        response = self.llm.chat(
            SYSTEM_PROMPT,
            self.context.trim(wrapped),
            self.registry.schemas(),
            tool_choice={"type": "none"},
        )
        return parse_response(response).thought or f"Stopped early ({reason}) without a final answer."