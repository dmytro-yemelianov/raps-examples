"""discover_ids — auto-discover real hub/project/account IDs."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass


@dataclass
class DiscoveredIds:
    """IDs discovered from the live APS environment."""

    hub_id: str = ""
    account_id: str = ""
    project_id: str = ""
    project_full_id: str = ""
    user_email: str = ""
    user_id: str = ""


def discover_ids(
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> DiscoveredIds:
    """Discover hub/project/account IDs by querying the RAPS CLI.

    Requires 3-legged auth to be active. Returns empty IDs on failure.
    """
    ids = DiscoveredIds()

    # Discover hubs — prefer BIM 360 hub
    try:
        proc = subprocess.run(
            "raps hub list --output json --quiet",
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
            env=env,
        )
        if proc.returncode == 0:
            hubs = json.loads(proc.stdout)
            # Prefer BIM 360 hub, then any b. hub, then first hub
            hub = None
            for h in hubs:
                if h.get("extension_type") == "BIM 360":
                    hub = h
                    break
            if not hub:
                for h in hubs:
                    if h.get("id", "").startswith("b."):
                        hub = h
                        break
            if not hub and hubs:
                hub = hubs[0]
            if hub:
                ids.hub_id = hub["id"]
                if ids.hub_id.startswith("b."):
                    ids.account_id = ids.hub_id[2:]
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, KeyError):
        pass

    # Discover first project in the hub
    if ids.hub_id:
        try:
            proc = subprocess.run(
                f"raps project list {ids.hub_id} --output json --quiet",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
                env=env,
            )
            if proc.returncode == 0:
                projects = json.loads(proc.stdout)
                if projects:
                    ids.project_full_id = projects[0]["id"]
                    if ids.project_full_id.startswith("b."):
                        ids.project_id = ids.project_full_id[2:]
                    else:
                        ids.project_id = ids.project_full_id
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, KeyError):
            pass

    # Discover current user
    try:
        proc = subprocess.run(
            "raps auth whoami --output json --quiet",
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=cwd,
            env=env,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout)
            ids.user_email = data.get("email", "")
            ids.user_id = data.get("aps_id", "")
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass

    return ids
