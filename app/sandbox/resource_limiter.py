"""Resource limits for sandboxed execution."""


def docker_limit_args(memory_mb: int) -> list:
    """Docker flags: no network, capped memory/CPU/processes, read-only FS, no privileges."""
    return [
        "--network", "none",
        "--memory", f"{memory_mb}m",
        "--memory-swap", f"{memory_mb}m",
        "--cpus", "0.5",
        "--pids-limit", "64",
        "--read-only",
        "--tmpfs", "/tmp:rw,size=64m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "65534:65534",
    ]


def make_preexec_fn(memory_mb: int, cpu_seconds: int):
    """For the subprocess fallback (Unix only). Returns None where `resource` is unavailable."""
    try:
        import resource
    except ImportError:
        return None

    def _apply():
        try:
            mem = memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
        except (ValueError, OSError):
            pass  # e.g. unsupported on macOS
        try:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
        except (ValueError, OSError):
            pass

    return _apply