from app.agent_core.stopping_criteria import StoppingCriteria


def test_keeps_going_under_limits():
    assert StoppingCriteria(5, 3).check(step=2, consecutive_errors=0) is None


def test_stops_at_max_iterations():
    assert StoppingCriteria(5, 3).check(step=5, consecutive_errors=0) == "max_iterations"


def test_stops_on_error_threshold():
    assert StoppingCriteria(5, 3).check(step=1, consecutive_errors=3) == "error_threshold"