""".yr script generation and parallel GIF rendering from collected command records."""

from __future__ import annotations

import math
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .runner import CommandRecord

# Patterns for resource creation commands that need cleanup preamble
_BUCKET_CREATE_RE = re.compile(r"raps bucket create -k (\S+)")
_WEBHOOK_CREATE_RE = re.compile(r"raps webhooks create")


def _find_yr_binary(cwd: str | None) -> str | None:
    """Return full path to yr binary built from yr repo, or fall back to PATH."""
    import shutil

    if cwd:
        examples_root = Path(cwd).resolve()
        workspace = examples_root.parent
        yr_root = workspace / "yr"
        for profile in ("release", "debug"):
            exe = yr_root / "target" / profile / ("yr.exe" if sys.platform == "win32" else "yr")
            if exe.is_file():
                return str(exe)
    # Fall back to yr on PATH (e.g. Docker container)
    found = shutil.which("yr")
    if found:
        return found
    return None


def _sleep_duration(actual: float) -> int:
    """Compute .yr Sleep duration: max(2, ceil(actual + 1)), capped at 8."""
    return min(8, max(2, math.ceil(actual + 1)))


def _escape_yr_string(s: str) -> str:
    """Escape a string for .yr Type command (handle double-quotes)."""
    return s.replace('"', '\\"')


class YrScriptGenerator:
    """Generate .yr scenario files from collected CommandRecords."""

    def __init__(
        self,
        *,
        shell: str | None = None,
        width: int = 100,
        height: int = 30,
        font_size: int = 14,
        theme: str = "dracula",
        typing_speed: str = "30ms",
    ) -> None:
        self.shell = shell or ("powershell -NoProfile" if sys.platform == "win32" else "bash")
        self.width = width
        self.height = height
        self.font_size = font_size
        self.theme = theme
        self.typing_speed = typing_speed

    @staticmethod
    def _build_cleanup(commands: list[CommandRecord]) -> list[str]:
        """Build cleanup commands to run before the main script.

        Scans for resource-creation commands and emits corresponding deletes
        so the recording starts from a clean state.
        """
        cleanup: list[str] = []
        seen_buckets: set[str] = set()

        for cmd in commands:
            if cmd.timed_out:
                continue
            m = _BUCKET_CREATE_RE.search(cmd.command)
            if m:
                bucket = m.group(1)
                if bucket not in seen_buckets:
                    seen_buckets.add(bucket)
                    cleanup.append(f"raps bucket delete {bucket} -y")

        return cleanup

    def _build_script(
        self,
        section_name: str,
        section_title: str,
        commands: list[CommandRecord],
    ) -> str:
        """Build a .yr script string for one section."""
        lines = [
            f"# Section: {section_name} — {section_title}",
            f'Set Shell "{self.shell}"',
            f"Set Width {self.width}",
            f"Set Height {self.height}",
            f"Set FontSize {self.font_size}",
            f'Set Theme "{self.theme}"',
            f"Set TypingSpeed {self.typing_speed}",
            f"Output recordings/{section_name}.gif",
            "",
        ]

        # Cleanup preamble — delete resources that will be created
        cleanup_cmds = self._build_cleanup(commands)
        if cleanup_cmds:
            lines.append("# --- Cleanup: ensure fresh state ---")
            lines.append("Hide")
            for c in cleanup_cmds:
                lines.append(f'Type "{_escape_yr_string(c)}"')
                lines.append("Enter")
                lines.append("Sleep 3s")
            lines.append('Type "clear"')
            lines.append("Enter")
            lines.append("Sleep 1s")
            lines.append("Show")
            lines.append("")

        for cmd in commands:
            if cmd.timed_out:
                lines.append(f"# Skipped (timed out): {cmd.sr_id} {cmd.slug}")
                lines.append("")
                continue

            lines.append(f'Marker "{cmd.sr_id}: {cmd.slug}"')
            lines.append(f'Type "{_escape_yr_string(cmd.command)}"')
            lines.append("Enter")
            sleep = _sleep_duration(cmd.duration)
            lines.append(f"Sleep {sleep}s")
            lines.append("")

        return "\n".join(lines)

    def generate_all(
        self,
        output_dir: Path,
        commands_by_section: dict[str, tuple[str, list[CommandRecord]]],
    ) -> list[Path]:
        """Generate .yr files for all sections.

        Args:
            output_dir: Directory to write .yr files to.
            commands_by_section: Mapping of section_name -> (section_title, commands).

        Returns:
            List of generated .yr file paths.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated: list[Path] = []

        for section_name, (title, commands) in sorted(commands_by_section.items()):
            # Skip sections with no usable commands
            usable = [c for c in commands if not c.timed_out]
            if not usable:
                continue

            script = self._build_script(section_name, title, commands)
            yr_path = output_dir / f"{section_name}.yr"
            yr_path.write_text(script, encoding="utf-8")
            generated.append(yr_path)

        return generated

    @staticmethod
    def render_all(
        yr_files: list[Path],
        yr_binary: str,
        workers: int = 4,
    ) -> dict[str, bool]:
        """Render .yr files to GIF in parallel.

        Returns:
            Mapping of filename -> success (True/False).
        """
        results: dict[str, bool] = {}

        def _render_one(yr_path: Path) -> tuple[str, bool, str]:
            try:
                # Run from project root so relative paths (./test-data/) resolve
                project_root = str(yr_path.parent.parent)
                proc = subprocess.run(
                    [yr_binary, "render", str(yr_path), "-q"],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    cwd=project_root,
                )
                return yr_path.name, proc.returncode == 0, proc.stderr
            except subprocess.TimeoutExpired:
                return yr_path.name, False, "render timed out after 600s"
            except Exception as exc:
                return yr_path.name, False, str(exc)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_render_one, f): f for f in yr_files}
            for future in as_completed(futures):
                name, ok, stderr = future.result()
                results[name] = ok
                if not ok:
                    sys.stderr.write(f"  yr render FAILED: {name}: {stderr}\n")

        return results
