"""Root conftest — fixtures, CLI options, and marker-based skip logic."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from .helpers.auth import AuthManager
from .helpers.discovery import DiscoveredIds, discover_ids
from .helpers.json_report import SectionJsonReporter
from .helpers.runner import RapsRunner, build_raps_env
from .helpers.test_users import TestUsers

# Prevent pytest from collecting helper modules as tests
collect_ignore = [str(Path(__file__).parent / "helpers")]


# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--mock",
        action="store_true",
        default=False,
        help="Run tests against raps-mock server instead of real APS",
    )
    parser.addoption(
        "--mock-port",
        type=int,
        default=3000,
        help="Port for raps-mock server (default: 3000)",
    )
    parser.addoption(
        "--raps-timeout",
        type=int,
        default=30,
        help="Default timeout in seconds for RAPS commands (default: 30)",
    )
    parser.addoption(
        "--json-report-dir",
        type=str,
        default=None,
        help="Directory for per-section JSON report files",
    )


# ---------------------------------------------------------------------------
# .env loading
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Load .env file."""
    try:
        from dotenv import load_dotenv

        # Look for .env in raps-examples root
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass


def pytest_sessionstart(session: pytest.Session) -> None:
    """Register JSON report plugin after CLI options are parsed."""
    report_dir = session.config.getoption("--json-report-dir", default=None)
    if report_dir:
        session.config.pluginmanager.register(
            SectionJsonReporter(Path(report_dir)),
            "section_json_reporter",
        )


# ---------------------------------------------------------------------------
# Marker-based skip logic
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip tests based on auth markers when auth is not available."""
    # Lazy — we just attach skip markers; actual check happens via fixtures


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Skip tests that require unavailable auth."""
    # require_2leg
    if list(item.iter_markers("require_2leg")):
        auth = getattr(item.session, "_auth_manager", None)
        if auth is not None and not auth.has_2leg():
            pytest.skip("2-legged auth not available")

    # require_3leg
    if list(item.iter_markers("require_3leg")):
        auth = getattr(item.session, "_auth_manager", None)
        if auth is not None and not auth.has_3leg():
            pytest.skip("3-legged auth not available")

    # require_acc
    if list(item.iter_markers("require_acc")):
        ids_obj = getattr(item.session, "_discovered_ids", None)
        if ids_obj is not None and not ids_obj.account_id:
            pytest.skip("No ACC account discovered")


# ---------------------------------------------------------------------------
# Auth status notification
# ---------------------------------------------------------------------------


def _notify_auth_status(mgr: AuthManager, target: str) -> None:
    """Warn the user early when authentication is missing."""
    if target == "mock":
        return

    has_2leg = mgr.has_2leg()
    has_3leg = mgr.has_3leg()

    if has_2leg and has_3leg:
        return

    lines = [
        "",
        "=" * 60,
        " RAPS Authentication Status",
        "=" * 60,
        f"  2-legged (client credentials): {'OK' if has_2leg else 'MISSING'}",
        f"  3-legged (user login):         {'OK' if has_3leg else 'MISSING'}",
        "-" * 60,
    ]
    if not has_2leg:
        lines.append("  Set APS_CLIENT_ID and APS_CLIENT_SECRET env vars")
    if not has_3leg:
        lines.append("  Run: raps auth login --preset all")
    lines += [
        "",
        "  Tests requiring missing auth will be skipped.",
        "=" * 60,
        "",
    ]
    sys.stderr.write("\n".join(lines) + "\n")

    if sys.stdin.isatty():
        try:
            answer = input("Continue? [Y/n] ").strip().lower()
        except EOFError:
            answer = ""
        if answer == "n":
            pytest.exit("Aborted by user — fix auth and re-run.", returncode=1)


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _target(request: pytest.FixtureRequest) -> str:
    return "mock" if request.config.getoption("--mock") else "real"


@pytest.fixture(scope="session")
def _mock_base_url(request: pytest.FixtureRequest) -> str:
    port = request.config.getoption("--mock-port")
    return f"http://localhost:{port}"


@pytest.fixture(scope="session")
def _raps_cwd() -> str:
    """Working directory for RAPS commands (raps-examples root)."""
    return str(Path(__file__).parent.parent)


@pytest.fixture(scope="session")
def _raps_env(_target: str, _raps_cwd: str, _mock_base_url: str) -> dict[str, str]:
    """Env dict with raps binary from workspace (../raps/target/release or debug)."""
    return build_raps_env(
        _raps_cwd,
        target=_target,
        mock_base_url=_mock_base_url,
    )


@pytest.fixture(scope="session")
def auth_manager(
    request: pytest.FixtureRequest, _target: str, _raps_cwd: str, _raps_env: dict[str, str]
) -> AuthManager:
    """Session-scoped auth manager with cached checks."""
    mgr = AuthManager(target=_target, cwd=_raps_cwd, env=_raps_env)
    # Save token before any destructive tests
    if _target != "mock":
        mgr.save_token()
    _notify_auth_status(mgr, _target)
    # Stash on session for marker-based skip logic
    request.session._auth_manager = mgr  # type: ignore[attr-defined]
    return mgr


@pytest.fixture(scope="session")
def ids(
    request: pytest.FixtureRequest,
    auth_manager: AuthManager,
    _target: str,
    _raps_cwd: str,
    _raps_env: dict[str, str],
) -> DiscoveredIds:
    """Discovered hub/project/account IDs (session-scoped)."""
    if _target == "mock":
        result = DiscoveredIds(
            hub_id="b.mock-hub-001",
            account_id="mock-hub-001",
            project_id="mock-project-001",
            project_full_id="b.mock-project-001",
            user_email="mock@example.com",
            user_id="mock-user-001",
        )
    elif auth_manager.has_3leg():
        result = discover_ids(cwd=_raps_cwd, env=_raps_env)
    else:
        result = DiscoveredIds()
    # Stash for marker-based skip
    request.session._discovered_ids = result  # type: ignore[attr-defined]
    return result


@pytest.fixture(scope="session")
def users() -> TestUsers:
    """Test user emails loaded from environment."""
    return TestUsers.from_env()


@pytest.fixture(scope="session")
def raps(
    _target: str, _mock_base_url: str, _raps_cwd: str, request: pytest.FixtureRequest
) -> RapsRunner:
    """Session-scoped RAPS CLI runner."""
    timeout = request.config.getoption("--raps-timeout")
    return RapsRunner(
        target=_target,
        mock_base_url=_mock_base_url,
        timeout=timeout,
        cwd=_raps_cwd,
    )


@pytest.fixture(scope="session", autouse=True)
def ensure_default_profile(raps: RapsRunner, _target: str) -> None:
    """Ensure 'default' profile exists and is active before config-dependent tests."""
    if _target == "mock":
        return
    # Create default if missing (create returns ok if already exists)
    raps.run("raps config profile create default", sr_id="", slug="ensure-default", may_fail=True)
    # Ensure default is active (use returns ok if already active)
    raps.run("raps config profile use default", sr_id="", slug="ensure-default-active", may_fail=True)


@pytest.fixture(scope="session")
def test_data(_raps_cwd: str) -> Path:
    """Path to the test-data directory, creating it if needed."""
    td = Path(_raps_cwd) / "test-data"
    td.mkdir(exist_ok=True)
    return td
