"""AuthManager — cached auth checks and token save/restore."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


class AuthManager:
    """Manage RAPS CLI authentication state for tests."""

    def __init__(
        self,
        *,
        target: str = "real",
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.target = target
        self.cwd = cwd
        self._env = env
        self._has_2leg: bool | None = None
        self._has_3leg: bool | None = None
        self._saved_token: str = ""

    def has_2leg(self) -> bool:
        """Check if 2-legged (client credentials) auth is available."""
        if self._has_2leg is None:
            if self.target == "mock":
                self._has_2leg = True
            else:
                try:
                    proc = subprocess.run(
                        "raps auth test --quiet",
                        shell=True,
                        capture_output=True,
                        timeout=15,
                        cwd=self.cwd,
                        env=self._env,
                    )
                    self._has_2leg = proc.returncode == 0
                except (subprocess.TimeoutExpired, OSError):
                    self._has_2leg = False
        return self._has_2leg

    def has_3leg(self) -> bool:
        """Check if 3-legged (user login) auth is available."""
        if self._has_3leg is None:
            if self.target == "mock":
                self._has_3leg = True
            else:
                try:
                    proc = subprocess.run(
                        "raps auth status --output json --quiet",
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=15,
                        cwd=self.cwd,
                        env=self._env,
                    )
                    if proc.returncode != 0:
                        self._has_3leg = False
                    else:
                        data = json.loads(proc.stdout or "{}")
                        self._has_3leg = (
                            data.get("three_legged", {}).get("logged_in") is True
                        )
                except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
                    self._has_3leg = False
        return self._has_3leg

    def save_token(self) -> None:
        """Save the current 3-legged token for later restoration.

        On Windows: reads from Credential Manager via runs/lib/read-token.ps1
        (RAPS keyring stores as username.service = aps_token.raps).
        On other platforms: uses raps auth inspect --output json (token may be masked).
        """
        try:
            if sys.platform == "win32":
                # Use read-token.ps1 which uses CredRead for aps_token.raps
                script = Path(self.cwd or ".") / "runs" / "lib" / "read-token.ps1"
                if script.exists():
                    proc = subprocess.run(
                        [
                            "powershell",
                            "-ExecutionPolicy",
                            "Bypass",
                            "-File",
                            str(script),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        cwd=self.cwd,
                    )
                    if proc.returncode == 0 and proc.stdout.strip():
                        self._saved_token = proc.stdout.strip()
            else:
                # Fallback: try auth inspect (token may be redacted on some platforms)
                proc = subprocess.run(
                    "raps -o json auth inspect",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=self.cwd,
                    env=self._env,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    data = json.loads(proc.stdout)
                    token = data.get("access_token")
                    if token and not (token.startswith("***") or "..." in token):
                        self._saved_token = token
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError, json.JSONDecodeError):
            pass

    def restore_token(self) -> None:
        """Restore saved 3-legged token after destructive operations."""
        self._has_2leg = None
        self._has_3leg = None

        if self._saved_token:
            try:
                subprocess.run(
                    f'raps auth login --token "{self._saved_token}"',
                    shell=True,
                    capture_output=True,
                    timeout=15,
                    cwd=self.cwd,
                    env=self._env,
                )
            except (subprocess.TimeoutExpired, OSError):
                pass

        # Re-check auth state
        self.has_2leg()
        self.has_3leg()

    def reset_cache(self) -> None:
        """Clear cached auth state so it gets re-checked."""
        self._has_2leg = None
        self._has_3leg = None
