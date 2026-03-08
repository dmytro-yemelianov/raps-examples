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
        """Check if 2-legged (client credentials) auth is available via env vars."""
        if self._has_2leg is None:
            if self.target == "mock":
                self._has_2leg = True
            else:
                env = self._env or os.environ
                self._has_2leg = bool(
                    env.get("APS_CLIENT_ID") and env.get("APS_CLIENT_SECRET")
                )
        return self._has_2leg

    def has_3leg(self) -> bool:
        """Check if 3-legged (user login) auth is available."""
        if self._has_3leg is None:
            if self.target == "mock":
                self._has_3leg = True
            else:
                self._has_3leg = self._check_3leg()
        return self._has_3leg

    def _check_3leg(self) -> bool:
        """Return True if a valid 3-legged session exists."""
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
                return False
            data = json.loads(proc.stdout or "{}")
            return data.get("three_legged", {}).get("logged_in") is True
        except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
            return False

    def ensure_3leg(self) -> bool:
        """Ensure 3-legged auth is available, opening browser login if needed.

        Returns True if logged in after this call.
        """
        if self.target == "mock":
            self._has_3leg = True
            return True

        if self._check_3leg():
            self._has_3leg = True
            return True

        sys.stderr.write("\n[raps] 3-legged auth required — opening browser login...\n")
        try:
            proc = subprocess.run(
                "raps auth login --preset all",
                shell=True,
                timeout=300,  # 5 min for the user to complete browser flow
                cwd=self.cwd,
                env=self._env,
            )
            if proc.returncode == 0:
                self._has_3leg = self._check_3leg()
            else:
                self._has_3leg = False
        except (subprocess.TimeoutExpired, OSError):
            self._has_3leg = False

        return bool(self._has_3leg)

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
                    "raps --output json auth inspect",
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

        token = self._saved_token
        # In mock mode, always use the well-known mock 3-legged token
        if not token and self.target == "mock":
            token = "mock-3leg-token"

        if token:
            try:
                subprocess.run(
                    f'raps auth login --token "{token}" --expires-in 86400 --preset all',
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
