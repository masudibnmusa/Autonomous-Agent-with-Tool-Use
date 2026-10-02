from types import SimpleNamespace as NS

from app.agent_core.action_parser import parse_response, parse_text_action


def test_parses_text_and_tool_use():
    response = NS(content=[
        NS(type="text", text="I need to calculate."),
        NS(type="tool_use", id="t1", name="calculator", input={"expression": "2+2"}),
    ])
    parsed = parse_response(response)
    assert parsed.thought == "I need to calculate."
    assert len(parsed.tool_calls) == 1
    assert parsed.tool_calls[0].name == "calculator"
    assert not parsed.is_final


def test_text_only_is_final():
    parsed = parse_response(NS(content=[NS(type="text", text="Done.")]))
    assert parsed.is_final
    assert parsed.thought == "Done."


def test_text_fallback_parser():
    assert parse_text_action('Action: {"tool": "calculator", "args": {"expression": "1+1"}}') == {
        "tool": "calculator",
        "args": {"expression": "1+1"},
    }
    assert parse_text_action("no json here") is None
    assert parse_text_action("{broken json") is None