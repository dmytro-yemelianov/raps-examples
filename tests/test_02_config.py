"""Configuration"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("02-config"),
]


# ── Atomic commands (ordered for profile create/switch/delete flow) ──


@pytest.mark.sr("SR-030")
def test_sr030_config_show(raps):
    raps.run_ok(
        "raps config profile export -n default",
        sr_id="SR-030",
        slug="config-show",
    )


@pytest.mark.sr("SR-031")
def test_sr031_config_get(raps):
    raps.run_ok("raps config get client_id", sr_id="SR-031", slug="config-get")


@pytest.mark.sr("SR-033")
def test_sr033_config_profile_create(raps):
    raps.run_ok(
        "raps config profile create staging",
        sr_id="SR-033",
        slug="config-profile-create",
    )


@pytest.mark.sr("SR-035")
def test_sr035_config_profile_use(raps):
    raps.run_ok(
        "raps config profile use staging",
        sr_id="SR-035",
        slug="config-profile-use",
    )


@pytest.mark.sr("SR-032")
def test_sr032_config_set(raps):
    raps.run_ok(
        "raps config set base_url https://developer.api.autodesk.com",
        sr_id="SR-032",
        slug="config-set",
    )


@pytest.mark.sr("SR-034")
def test_sr034_config_profile_list(raps):
    raps.run_ok(
        "raps config profile list",
        sr_id="SR-034",
        slug="config-profile-list",
    )


@pytest.mark.sr("SR-036")
def test_sr036_config_profile_current(raps):
    raps.run_ok(
        "raps config profile current",
        sr_id="SR-036",
        slug="config-profile-current",
    )


@pytest.mark.sr("SR-037")
def test_sr037_config_profile_export(raps):
    raps.run_ok(
        "raps config profile export -n staging",
        sr_id="SR-037",
        slug="config-profile-export",
    )


@pytest.mark.sr("SR-038")
def test_sr038_config_profile_import(raps):
    raps.run(
        "New-Item -ItemType Directory -Force -Path ./tmp | Out-Null"
        "; raps config profile export -o ./tmp/raps-staging-export.json -n staging"
        "; raps config profile import ./tmp/raps-staging-export.json --overwrite"
        "; Remove-Item -Force ./tmp/raps-staging-export.json",
        sr_id="SR-038",
        slug="config-profile-import",
    )


@pytest.mark.sr("SR-039")
def test_sr039_config_profile_diff(raps):
    raps.run_ok(
        "raps config profile diff default staging",
        sr_id="SR-039",
        slug="config-profile-diff",
    )


@pytest.mark.sr("SR-041")
def test_sr041_config_context_show(raps):
    raps.run_ok(
        "raps config context show",
        sr_id="SR-041",
        slug="config-context-show",
    )


@pytest.mark.sr("SR-042")
def test_sr042_config_context_set(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    project_full_id = ids.project_full_id or "b.demo-project-001"
    raps.run_ok(
        f"raps config context set hub_id {hub_id}; raps config context set project_id {project_full_id}",
        sr_id="SR-042",
        slug="config-context-set",
    )


@pytest.mark.sr("SR-043")
def test_sr043_config_context_clear(raps):
    raps.run_ok(
        "raps config context clear",
        sr_id="SR-043",
        slug="config-context-clear",
    )


def test_cleanup_staging_copy(raps):
    """Cleanup: delete staging-copy profile if it was created."""
    raps.run(
        "raps config profile delete staging-copy",
        sr_id="",
        slug="cleanup-staging-copy",
    )


@pytest.mark.sr("SR-040")
def test_sr040_config_profile_delete(raps):
    raps.run_ok(
        "raps config profile delete staging",
        sr_id="SR-040",
        slug="config-profile-delete",
    )


def test_cleanup_switch_to_default(raps):
    """Cleanup: switch back to default profile."""
    raps.run(
        "raps config profile use default",
        sr_id="",
        slug="cleanup-switch-default",
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-044")
@pytest.mark.lifecycle
def test_sr044_config_profile_lifecycle(raps):
    lc = raps.lifecycle("SR-044", "config-profile-lifecycle", "Full profile CRUD lifecycle")
    lc.step("raps config profile create test-lifecycle")
    lc.step("raps config profile use test-lifecycle")
    # Note: output_format is not a valid config key; use base_url instead
    lc.step("raps config set base_url http://localhost:9999")
    lc.step("raps config get base_url")
    lc.step("raps config profile export -n test-lifecycle")
    lc.step("raps config profile use default")
    lc.step("raps config profile delete test-lifecycle")
    lc.assert_all_passed()


@pytest.mark.sr("SR-045")
@pytest.mark.lifecycle
def test_sr045_config_context_lifecycle(raps, ids):
    hub_id = ids.hub_id or "b.demo-hub-001"
    project_full_id = ids.project_full_id or "b.demo-project-001"
    lc = raps.lifecycle(
        "SR-045", "config-context-lifecycle", "Context set and clear lifecycle"
    )
    lc.step("raps config profile create ctx-test")
    lc.step("raps config profile use ctx-test")
    lc.step(
        f"raps config context set hub_id {hub_id}"
        f"; raps config context set project_id {project_full_id}",
    )
    lc.step("raps config context show")
    lc.step("raps config context clear")
    lc.step("raps config context show")
    lc.step("raps config profile use default")
    lc.step("raps config profile delete ctx-test")
    lc.assert_all_passed()
