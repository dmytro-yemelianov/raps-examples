"""RapsRunner — subprocess wrapper for RAPS CLI sample runs."""

from __future__ import annotations

import functools
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Module-level log accumulator for JSON report integration
# ---------------------------------------------------------------------------
# Maps base SR-ID (e.g. "SR-063") -> accumulated log text.
# Lifecycle steps ("SR-063/step1") are folded into the base ID.
_captured_logs: dict[str, str] = {}
_captured_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Command record collector for .yr generation
# ---------------------------------------------------------------------------


@dataclass
class CommandRecord:
    """Structured record of a CLI invocation for .yr script generation."""

    sr_id: str
    slug: str
    command: str       # original command (before path resolution)
    duration: float
    exit_code: int
    timed_out: bool


_command_records: list[CommandRecord] = []
_commands_lock = threading.Lock()


def get_command_records() -> list[CommandRecord]:
    """Return a snapshot of collected command records."""
    with _commands_lock:
        return list(_command_records)


def clear_command_records() -> None:
    """Clear collected command records."""
    with _commands_lock:
        _command_records.clear()


def _store_log(sr_id: str, result: "RunResult") -> None:
    """Accumulate formatted log output for a sample run."""
    if not sr_id:
        return
    base_id = sr_id.split("/")[0]
    status = "TIMEOUT" if result.timed_out else f"exit {result.exit_code}"
    lines = [f"[{sr_id}] {result.slug}: {result.command}"]
    lines.append(f"  -> {status} ({result.duration}s)")
    if result.stdout.strip():
        lines.append(result.stdout.strip()[:3000])
    if result.stderr.strip():
        lines.append(f"  stderr: {result.stderr.strip()[:1000]}")
    lines.append("")
    entry = "\n".join(lines)
    with _captured_lock:
        _captured_logs.setdefault(base_id, "")
        _captured_logs[base_id] += entry


def clear_captured_logs() -> None:
    """Clear accumulated logs (called between sessions if needed)."""
    with _captured_lock:
        _captured_logs.clear()


@functools.cache
def _find_bash() -> str | None:
    """Return path to bash if on Windows, else None (Unix shell is fine)."""
    if sys.platform != "win32":
        return None
    # Prefer Git-for-Windows bash
    bash = shutil.which("bash")
    if bash:
        return bash
    git_bash = os.path.expandvars(r"%ProgramFiles%\Git\bin\bash.exe")
    if os.path.isfile(git_bash):
        return git_bash
    return None


# Shell metacharacters that require bash -c wrapping
_NEEDS_SHELL_RE = re.compile(r'[|&;<>`$]|2>&1|/dev/')


def _raps_bin_dir(cwd: str | None) -> str | None:
    """Return directory containing raps binary built from raps repo, or None."""
    if not cwd:
        return None
    from pathlib import Path

    # raps-examples is under workspace; raps CLI is at ../raps
    examples_root = Path(cwd).resolve()
    workspace = examples_root.parent
    raps_root = workspace / "raps"
    # Prefer release (faster runtime), fall back to debug
    for profile in ("release", "debug"):
        bindir = raps_root / "target" / profile
        exe = bindir / ("raps.exe" if sys.platform == "win32" else "raps")
        if exe.is_file():
            return str(bindir)
    return None


def _raps_binary(cwd: str | None) -> str | None:
    """Return full path to raps binary built from raps repo, or None."""
    if not cwd:
        return None
    from pathlib import Path

    examples_root = Path(cwd).resolve()
    workspace = examples_root.parent
    raps_root = workspace / "raps"
    for profile in ("release", "debug"):
        exe = raps_root / "target" / profile / ("raps.exe" if sys.platform == "win32" else "raps")
        if exe.is_file():
            return str(exe)
    return None


def build_raps_env(
    cwd: str | None,
    *,
    target: str = "real",
    mock_base_url: str = "http://localhost:3000",
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build env dict for raps subprocesses (PATH, .env, mock settings)."""
    env = dict(base_env) if base_env else dict(os.environ)
    if cwd:
        try:
            from pathlib import Path

            env_path = Path(cwd) / ".env"
            if env_path.exists():
                from dotenv import dotenv_values

                for k, v in dotenv_values(env_path).items():
                    if k and v is not None and k not in env:
                        env[k] = str(v)
        except (OSError, ImportError):
            pass
    if target == "mock":
        env["APS_BASE_URL"] = mock_base_url
        env.setdefault("APS_CLIENT_ID", "mock-client-id")
        env.setdefault("APS_CLIENT_SECRET", "mock-client-secret")
    raps_dir = _raps_bin_dir(cwd)
    if raps_dir:
        existing = env.get("PATH", "")
        sep = ";" if sys.platform == "win32" else ":"
        env["PATH"] = raps_dir + sep + existing
    return env


def _path_for_bash(path: str, bash: str | None) -> str:
    """Convert Windows path to format bash can resolve (WSL vs Git Bash)."""
    path = path.replace("\\", "/")
    if sys.platform != "win32":
        return path
    # WSL bash (System32\bash.exe) expects /mnt/c/...; Git Bash understands C:/
    bash_norm = (bash or "").replace("/", "\\").lower()
    if "system32" in bash_norm and ("bash" in bash_norm or "wsl" in bash_norm):
        if len(path) >= 2 and path[1] == ":":
            drive = path[0].lower()
            rest = path[2:].lstrip("/")
            return f"/mnt/{drive}/{rest}"
    return path


def _resolve_raps_command(command: str, raps_bin: str | None, bash: str | None = None) -> str:
    """Replace leading 'raps ' with full binary path for reliable resolution."""
    if not raps_bin or not command.strip().startswith("raps "):
        return command
    path = _path_for_bash(raps_bin, bash)
    if " " in path:
        path = f'"{path}"'
    return path + " " + command[5:]


@dataclass
class RunResult:
    """Result of a single RAPS CLI invocation."""

    sr_id: str
    slug: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class LifecycleContext:
    """Multi-step lifecycle test context."""

    def __init__(
        self,
        runner: RapsRunner,
        sr_id: str,
        slug: str,
        description: str,
    ) -> None:
        self.runner = runner
        self.sr_id = sr_id
        self.slug = slug
        self.description = description
        self.results: list[RunResult] = []
        self._step_num = 0

    def step(self, command: str) -> RunResult:
        """Execute a lifecycle step and record its result."""
        self._step_num += 1
        result = self.runner.run(
            command,
            sr_id=f"{self.sr_id}/step{self._step_num}",
            slug=f"{self.slug}-step{self._step_num}",
        )
        self.results.append(result)
        return result

    def assert_all_passed(self) -> None:
        """Assert that all lifecycle steps passed."""
        failures = [r for r in self.results if not r.ok]
        if failures:
            lines = [
                f"Lifecycle {self.sr_id} ({self.slug}): "
                f"{len(failures)}/{len(self.results)} steps failed"
            ]
            for r in failures:
                status = "TIMEOUT" if r.timed_out else f"exit {r.exit_code}"
                lines.append(f"  {r.sr_id}: {r.command} -> {status}")
                if r.stderr.strip():
                    # Show first 200 chars of stderr
                    lines.append(f"    stderr: {r.stderr.strip()[:200]}")
            raise AssertionError("\n".join(lines))


class RapsRunner:
    """Execute RAPS CLI commands as subprocesses with mock routing."""

    def __init__(
        self,
        *,
        target: str = "real",
        mock_base_url: str = "http://localhost:3000",
        timeout: int = 30,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.target = target
        self.mock_base_url = mock_base_url
        self.timeout = timeout
        self.cwd = cwd
        self._env = build_raps_env(
            cwd,
            target=target,
            mock_base_url=mock_base_url,
            base_env=dict(env) if env else None,
        )
        self._raps_bin = _raps_binary(cwd)

    def run(
        self,
        command: str,
        *,
        sr_id: str = "",
        slug: str = "",
        timeout: int | None = None,
    ) -> RunResult:
        """Run a command and return the result."""
        original_command = command  # preserve before path resolution
        effective_timeout = timeout or self.timeout
        bash = _find_bash()

        # Determine execution strategy: direct (fast) vs bash -c (shell features)
        needs_shell = bool(_NEEDS_SHELL_RE.search(command))

        if needs_shell:
            # Shell features needed — route through bash
            resolved = _resolve_raps_command(command, self._raps_bin, bash)
            cmd_args = [bash, "-c", resolved] if bash else resolved
            use_shell = not bash
        elif self._raps_bin and command.strip().startswith("raps "):
            # Simple raps command — run binary directly (skip bash overhead)
            argv = command.strip().split(None, 1)
            raps_args = argv[1] if len(argv) > 1 else ""
            cmd_args = [self._raps_bin] + shlex.split(raps_args)
            use_shell = False
            command = _resolve_raps_command(command, self._raps_bin, bash)
        else:
            # Non-raps simple command
            resolved = _resolve_raps_command(command, self._raps_bin, bash)
            cmd_args = [bash, "-c", resolved] if bash else resolved
            use_shell = not bash

        start = time.monotonic()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd_args,
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=self.cwd,
                env=self._env,
            )
            exit_code = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = 124
            stdout = ""
            stderr = f"TIMEOUT after {effective_timeout}s"
        duration = round(time.monotonic() - start, 2)

        result = RunResult(
            sr_id=sr_id,
            slug=slug,
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration=duration,
            timed_out=timed_out,
        )
        _store_log(sr_id, result)

        # Collect original command for .yr generation
        if sr_id:
            with _commands_lock:
                _command_records.append(CommandRecord(
                    sr_id=sr_id,
                    slug=slug,
                    command=original_command,
                    duration=duration,
                    exit_code=exit_code,
                    timed_out=timed_out,
                ))

        return result

    def run_ok(
        self,
        command: str,
        *,
        sr_id: str = "",
        slug: str = "",
        timeout: int | None = None,
    ) -> RunResult:
        """Run a command and assert exit code 0."""
        result = self.run(command, sr_id=sr_id, slug=slug, timeout=timeout)
        assert result.ok, (
            f"[{sr_id}] {slug}: expected exit 0, got {result.exit_code}\n"
            f"  command: {result.command}\n"
            f"  stderr:  {result.stderr.strip()[:500]}"
        )
        return result

    def lifecycle(
        self,
        sr_id: str,
        slug: str,
        description: str,
    ) -> LifecycleContext:
        """Create a lifecycle context for multi-step tests."""
        return LifecycleContext(self, sr_id, slug, description)
