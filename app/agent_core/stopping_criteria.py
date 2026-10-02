"""When should the loop stop?

Completion (no tool calls from the model) is handled in the loop itself.
This class handles the safety limits.
"""
from typing import Optional


class StoppingCriteria:
    def __init__(self, max_iterations: int = 15, max_consecutive_errors: int = 3):
        self.max_iterations = max_iterations
        self.max_consecutive_errors = max_consecutive_errors

    def check(self, step: int, consecutive_errors: int) -> Optional[str]:
        """Return a stop reason string, or None to keep going."""
        if consecutive_errors >= self.max_consecutive_errors:
            return "error_threshold"
        if step >= self.max_iterations:
            return "max_iterations"
        return None