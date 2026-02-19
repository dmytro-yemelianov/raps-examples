"""Authentication"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("01-auth"),
]

EXTERNAL_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.demo-token-for-testing"


# ── Atomic commands ──────────────────────────────────────────────


@pytest.mark.sr("SR-010")
def test_sr010_auth_test_2leg(raps):
    raps.run("raps auth test", sr_id="SR-010", slug="auth-test-2leg")


@pytest.mark.sr("SR-011")
def test_sr011_auth_login_3leg_browser():
    pytest.skip("oauth_auto_login not available in pytest")


@pytest.mark.sr("SR-012")
def test_sr012_auth_login_device_code(raps):
    raps.run(
        "raps auth login --device 2>&1",
        sr_id="SR-012",
        slug="auth-login-device-code",
        timeout=5,
    )


@pytest.mark.sr("SR-013")
def test_sr013_auth_login_token_direct(raps):
    # Extract current token and re-inject it
    result = raps.run(
        "raps --output json auth inspect",
        sr_id="SR-013",
        slug="auth-login-token-direct-inspect",
    )
    token = EXTERNAL_TOKEN
    if result.ok and result.stdout.strip():
        try:
            import json

            data = json.loads(result.stdout)
            token = data.get("access_token", EXTERNAL_TOKEN) or EXTERNAL_TOKEN
        except (json.JSONDecodeError, KeyError):
            pass
    raps.run(
        f'raps auth login --token "{token}"',
        sr_id="SR-013",
        slug="auth-login-token-direct",
    )


@pytest.mark.sr("SR-014")
def test_sr014_auth_login_refresh_token(raps):
    # Extract refresh token if 3-leg is active; otherwise use dummy
    result = raps.run(
        "raps --output json auth inspect",
        sr_id="SR-014",
        slug="auth-login-refresh-token-inspect",
    )
    refresh = "dummy-refresh"
    if result.ok and result.stdout.strip():
        try:
            import json

            data = json.loads(result.stdout)
            refresh = data.get("refresh_token", "dummy-refresh") or "dummy-refresh"
        except (json.JSONDecodeError, KeyError):
            pass
    raps.run(
        f'raps auth login --refresh-token "{refresh}" --expires-in 3600',
        sr_id="SR-014",
        slug="auth-login-refresh-token",
    )


@pytest.mark.sr("SR-015")
def test_sr015_auth_status(raps):
    raps.run(
        "raps auth status",
        sr_id="SR-015",
        slug="auth-status",
    )


@pytest.mark.sr("SR-016")
def test_sr016_auth_whoami(raps):
    raps.run(
        "raps auth whoami",
        sr_id="SR-016",
        slug="auth-whoami",
    )


@pytest.mark.sr("SR-017")
def test_sr017_auth_inspect(raps):
    raps.run(
        "raps auth inspect",
        sr_id="SR-017",
        slug="auth-inspect",
    )


@pytest.mark.sr("SR-018")
def test_sr018_auth_inspect_warn(raps):
    raps.run(
        "raps auth inspect --warn-expiry-seconds 86400",
        sr_id="SR-018",
        slug="auth-inspect-warn",
    )


@pytest.mark.sr("SR-019")
def test_sr019_auth_logout(raps, auth_manager):
    raps.run("raps auth logout", sr_id="SR-019", slug="auth-logout")
    auth_manager.restore_token()


@pytest.mark.sr("SR-020")
def test_sr020_auth_login_default_profile():
    pytest.skip("oauth_auto_login not available in pytest")


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-021")
@pytest.mark.lifecycle
def test_sr021_auth_lifecycle_2leg(raps, auth_manager):
    lc = raps.lifecycle("SR-021", "auth-lifecycle-2leg", "Full 2-legged auth cycle")
    lc.step("raps auth test")
    lc.step("raps auth status")
    lc.step("raps auth inspect")
    lc.step("raps auth logout")
    lc.step("raps auth test")
    lc.assert_all_passed()
    auth_manager.restore_token()


@pytest.mark.sr("SR-022")
def test_sr022_auth_lifecycle_3leg():
    pytest.skip("interactive (opens browser)")


@pytest.mark.sr("SR-023")
def test_sr023_auth_lifecycle_device(raps):
    raps.run(
        "raps auth login --device 2>&1",
        sr_id="SR-023",
        slug="auth-lifecycle-device",
        timeout=5,
    )


@pytest.mark.sr("SR-024")
@pytest.mark.lifecycle
def test_sr024_auth_lifecycle_token_injection(raps, auth_manager):
    # Extract a real token for injection — skip if none available
    inspect_result = raps.run(
        "raps --output json auth inspect",
        sr_id="SR-024",
        slug="auth-lifecycle-token-injection-inspect",
    )
    token = ""
    if inspect_result.ok and inspect_result.stdout.strip():
        try:
            import json

            data = json.loads(inspect_result.stdout)
            token = data.get("access_token", "") or ""
        except (json.JSONDecodeError, KeyError):
            pass

    if not token:
        pytest.skip("No valid token available for injection test (requires 3-leg auth)")

    lc = raps.lifecycle(
        "SR-024", "auth-lifecycle-token-injection", "Token injection cycle"
    )
    lc.step(f'raps auth login --token "{token}"')
    lc.step("raps auth test")
    lc.step("raps auth status")
    lc.step("raps auth inspect")
    lc.step("raps auth logout")
    lc.assert_all_passed()
    auth_manager.restore_token()
