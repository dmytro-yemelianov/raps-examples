"""Root conftest — fixtures, CLI options, and marker-based skip logic."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

from .helpers.auth import AuthManager
from .helpers.discovery import DiscoveredIds, discover_ids
from .helpers.json_report import SectionJsonReporter
from .helpers.runner import CommandRecord, RapsRunner, build_raps_env, get_command_records, clear_command_records
from .helpers.test_users import TestUsers
from .helpers.yr_generator import YrScriptGenerator, _find_yr_binary

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
    parser.addoption(
        "--generate-yr",
        action="store_true",
        default=False,
        help="Generate .yr scenario files from test commands",
    )
    parser.addoption(
        "--render-yr",
        action="store_true",
        default=False,
        help="Also render .yr files to GIF (implies --generate-yr)",
    )
    parser.addoption(
        "--yr-output-dir",
        type=str,
        default="recordings",
        help="Output directory for .yr and .gif files (default: recordings)",
    )
    parser.addoption(
        "--yr-workers",
        type=int,
        default=4,
        help="Parallel workers for yr rendering (default: 4)",
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
    """Register plugins after CLI options are parsed."""
    report_dir = session.config.getoption("--json-report-dir", default=None)
    if report_dir:
        session.config.pluginmanager.register(
            SectionJsonReporter(Path(report_dir)),
            "section_json_reporter",
        )

    generate_yr = session.config.getoption("--generate-yr", default=False)
    render_yr = session.config.getoption("--render-yr", default=False)
    if generate_yr or render_yr:
        output_dir = Path(session.config.getoption("--yr-output-dir"))
        workers = session.config.getoption("--yr-workers")
        cwd = str(Path(__file__).parent.parent)
        session.config.pluginmanager.register(
            YrRecorderPlugin(
                output_dir=output_dir,
                render=render_yr,
                workers=workers,
                cwd=cwd,
            ),
            "yr_recorder",
        )


# ---------------------------------------------------------------------------
# .yr recording plugin
# ---------------------------------------------------------------------------


class YrRecorderPlugin:
    """Pytest plugin that generates .yr scripts and optionally renders GIFs."""

    def __init__(
        self,
        output_dir: Path,
        render: bool,
        workers: int,
        cwd: str,
    ) -> None:
        self.output_dir = output_dir
        self.render = render
        self.workers = workers
        self.cwd = cwd
        # section_name -> (section_title, list of CommandRecord)
        self._sections: dict[str, tuple[str, list[CommandRecord]]] = {}

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call):
        outcome = yield
        report = outcome.get_result()

        if report.when != "call":
            return

        # Derive section name from module (same logic as json_report.py)
        module_name = item.module.__name__.rsplit(".", 1)[-1]
        m = re.match(r"test_(\d+)_(.+)", module_name)
        if not m:
            return
        section_num = m.group(1)
        section_slug = m.group(2).replace("_", "-")
        section_name = f"{section_num}-{section_slug}"

        # Get section title from module docstring
        if section_name not in self._sections:
            title = ""
            if item.module.__doc__:
                title = item.module.__doc__.strip().split("\n")[0]
            if not title:
                title = section_name
            self._sections[section_name] = (title, [])

        # Extract SR ID from markers
        sr_id = ""
        for marker in item.iter_markers("sr"):
            sr_id = marker.args[0] if marker.args else ""
            break

        if not sr_id:
            return

        # Find matching command records for this test's sr_id
        base_id = sr_id.split("/")[0]
        for rec in get_command_records():
            rec_base = rec.sr_id.split("/")[0]
            if rec_base == base_id:
                # Avoid duplicates (lifecycle steps share base ID)
                existing = self._sections[section_name][1]
                if not any(r.sr_id == rec.sr_id and r.command == rec.command for r in existing):
                    existing.append(rec)

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Generate .yr files and optionally render GIFs."""
        if not self._sections:
            return

        generator = YrScriptGenerator()
        yr_files = generator.generate_all(self.output_dir, self._sections)

        n_generated = len(yr_files)
        sys.stderr.write(f"\nyr: Generated {n_generated} .yr files in {self.output_dir}/\n")

        if self.render and yr_files:
            yr_bin = _find_yr_binary(self.cwd)
            if not yr_bin:
                sys.stderr.write("yr: WARNING — yr binary not found, skipping render\n")
                return

            sys.stderr.write(f"yr: Rendering {n_generated} GIFs with {self.workers} workers...\n")
            results = YrScriptGenerator.render_all(yr_files, yr_bin, self.workers)
            ok = sum(1 for v in results.values() if v)
            fail = sum(1 for v in results.values() if not v)
            sys.stderr.write(f"yr: Rendered {ok} GIFs")
            if fail:
                sys.stderr.write(f" ({fail} failed)")
            sys.stderr.write(f" in {self.output_dir}/\n")

        clear_command_records()


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
    raps.run("raps config profile create default", sr_id="", slug="ensure-default")
    # Ensure default is active (use returns ok if already active)
    raps.run("raps config profile use default", sr_id="", slug="ensure-default-active")


@pytest.fixture(scope="session")
def test_data(_raps_cwd: str) -> Path:
    """Path to the test-data directory, creating it if needed."""
    td = Path(_raps_cwd) / "test-data"
    td.mkdir(exist_ok=True)
    return td
