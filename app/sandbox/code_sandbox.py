"""Isolated Python execution.

Mode "docker": real isolation (recommended).
Mode "subprocess": a weak fallback for local dev ONLY. It is not a security boundary.
"""
import os
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass

from app import config
from app.sandbox.resource_limiter import docker_limit_args, make_preexec_fn

MAX_OUTPUT_CHARS = 5000


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool = False

    def format(self) -> str:
        if self.timed_out:
            return f"Execution timed out.\n{self.stderr}".strip()
        parts = []
        if self.stdout:
            parts.append(f"STDOUT:\n{self.stdout[:MAX_OUTPUT_CHARS]}")
        if self.stderr:
            parts.append(f"STDERR:\n{self.stderr[:MAX_OUTPUT_CHARS]}")
        parts.append(f"Exit code: {self.exit_code}")
        return "\n".join(parts)


class CodeSandbox:
    def __init__(self, mode: str = None, image: str = None, timeout: int = None, memory_mb: int = None):
        self.mode = mode or config.SANDBOX_MODE
        self.image = image or config.SANDBOX_IMAGE
        self.timeout = timeout or config.SANDBOX_TIMEOUT_SEC
        self.memory_mb = memory_mb or config.SANDBOX_MEMORY_MB

    def run_python(self, code: str) -> SandboxResult:
        if self.mode == "docker":
            return self._run_docker(code)
        return self._run_subprocess(code)

    def _run_docker(self, code: str) -> SandboxResult:
        name = f"agent-sbx-{uuid.uuid4().hex[:12]}"
        cmd = ["docker", "run", "--rm", "-i", "--name", name,
               *docker_limit_args(self.memory_mb), self.image, "python", "-"]
        try:
            # A few extra seconds of slack for container startup
            proc = subprocess.run(cmd, input=code, capture_output=True, text=True,
                                  timeout=self.timeout + 5)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", name], capture_output=True)
            return SandboxResult("", f"Exceeded {self.timeout}s limit.", -1, True)
        except FileNotFoundError:
            return SandboxResult("", "Docker is not installed or not on PATH.", -1)
        return SandboxResult(proc.stdout, proc.stderr, proc.returncode)

    def _run_subprocess(self, code: str) -> SandboxResult:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmp,
                    env={"PATH": os.environ.get("PATH", "")},  # don't leak API keys
                    preexec_fn=make_preexec_fn(self.memory_mb, self.timeout + 1),
                )
            except subprocess.TimeoutExpired:
                return SandboxResult("", f"Exceeded {self.timeout}s limit.", -1, True)
        return SandboxResult(proc.stdout, proc.stderr, proc.returncode)