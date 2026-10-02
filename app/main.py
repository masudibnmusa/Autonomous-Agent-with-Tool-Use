"""Entry point: CLI (python -m app.main --goal "...") or Streamlit (streamlit run app/main.py)."""
import argparse
import json
import sys
from pathlib import Path

# Make `app` importable when launched via `streamlit run app/main.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config
from app.agent_core.agent_loop import Agent
from app.agent_core.planner import Planner
from app.agent_core.stopping_criteria import StoppingCriteria
from app.llm.llm_client import LLMClient
from app.memory.context_manager import ContextManager
from app.safety.action_validator import ActionValidator
from app.safety.human_approval import HumanApproval
from app.tools.registry import build_default_registry
from app.utils.trace_logger import TraceLogger


def build_agent(approver, on_event=None, use_planner=None, max_iterations=None) -> Agent:
    llm = LLMClient()
    registry = build_default_registry()
    validator = ActionValidator(registry.names(), require_approval=config.REQUIRE_APPROVAL)
    criteria = StoppingCriteria(
        max_iterations or config.MAX_ITERATIONS, config.MAX_CONSECUTIVE_ERRORS
    )
    planner = Planner(llm) if (config.USE_PLANNER if use_planner is None else use_planner) else None
    return Agent(
        llm=llm,
        registry=registry,
        validator=validator,
        approver=approver,
        criteria=criteria,
        context_manager=ContextManager(keep_last=config.CONTEXT_KEEP_LAST),
        logger=TraceLogger(),
        planner=planner,
        on_event=on_event,
    )


def cli_event(e: dict) -> None:
    if e["type"] == "plan":
        print(f"\n[Plan]\n{e['plan']}\n")
    elif e["type"] == "step":
        flag = " (error)" if e["is_error"] else ""
        print(f"[Step {e['index']}] Thought: {e['thought'] or '(none)'}")
        print(f"         Action:  {e['tool']}({json.dumps(e['args'])[:200]})")
        print(f"         Result:  {e['observation'][:200]!r}{flag}\n")
    elif e["type"] == "final":
        print(f"=== Final Answer ({e['stop_reason']}) ===\n{e['answer']}\n")


def run_cli() -> None:
    parser = argparse.ArgumentParser(description="Autonomous tool-using agent")
    parser.add_argument("--goal", required=True, help="Task for the agent")
    parser.add_argument("--planner", action="store_true", help="Create an upfront plan")
    parser.add_argument("--auto-approve", action="store_true", help="Skip approval prompts")
    parser.add_argument("--max-iterations", type=int, default=None)
    args = parser.parse_args()

    if not config.ANTHROPIC_API_KEY:
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in.")

    agent = build_agent(
        HumanApproval(auto_approve=args.auto_approve),
        on_event=cli_event,
        use_planner=args.planner or None,
        max_iterations=args.max_iterations,
    )
    result = agent.run(args.goal)
    print(f"Trace saved to {result.trace_path}")


def run_streamlit() -> None:
    import streamlit as st

    st.set_page_config(page_title="Autonomous Agent", layout="wide")
    st.title("Autonomous Agent")

    goal = st.text_area("Goal", placeholder="Find the top 5 Python web frameworks by GitHub stars...")
    use_planner = st.sidebar.checkbox("Use planner", value=config.USE_PLANNER)
    auto = st.sidebar.checkbox("Auto-approve sensitive actions", value=False)
    st.sidebar.caption("If unchecked, sensitive actions are denied in the web UI.")

    if st.button("Run", type="primary") and goal.strip():
        if not config.ANTHROPIC_API_KEY:
            st.error("ANTHROPIC_API_KEY is not set.")
            st.stop()

        container = st.container()

        def on_event(e: dict) -> None:
            with container:
                if e["type"] == "plan":
                    st.info(e["plan"])
                elif e["type"] == "step":
                    label = f"Step {e['index']}: {e['tool']}" + (" (error)" if e["is_error"] else "")
                    with st.expander(label):
                        if e["thought"]:
                            st.markdown(f"**Thought:** {e['thought']}")
                        st.code(json.dumps(e["args"], indent=2), language="json")
                        st.text(e["observation"][:1500])

        approver = HumanApproval(auto_approve=auto, callback=lambda tool, args, reason: False)
        agent = build_agent(approver, on_event=on_event, use_planner=use_planner)
        with st.spinner("Agent working..."):
            result = agent.run(goal)

        st.subheader(f"Final answer ({result.stop_reason})")
        st.markdown(result.answer)
        st.caption(f"Trace: {result.trace_path}")


def _in_streamlit() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


if __name__ == "__main__":
    if _in_streamlit():
        run_streamlit()
    else:
        run_cli()