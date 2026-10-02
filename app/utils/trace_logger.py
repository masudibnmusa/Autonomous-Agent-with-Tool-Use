"""Save the full agent trajectory for debugging and transparency."""
import json
from datetime import datetime
from pathlib import Path

from app import config


class TraceLogger:
    def __init__(self, trace_dir: Path = None):
        self.trace_dir = Path(trace_dir or config.TRACE_DIR)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

    def save(self, goal: str, pad, answer: str, stop_reason: str, model: str = "") -> str:
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = self.trace_dir / f"run_{stamp}.json"
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "model": model,
            "goal": goal,
            "stop_reason": stop_reason,
            "final_answer": answer,
            **pad.to_dict(),
        }
        path.write_text(json.dumps(payload, indent=2))
        return str(path)