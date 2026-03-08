"""Configuration"""

import time

import pytest

_TS = str(int(time.time()))
SNAP_BUCKET = f"sr-snap-{_TS}"

pytestmark = [
    pytest.mark.xdist_group("02-config"),
]


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-038")
def test_sr038_config_profile_import(raps):
    raps.run(
        "New-Item -ItemType Directory -Force -Path ./tmp | Out-Null"
        "; raps config profile export --out-file ./tmp/raps-staging-export.json -n staging"
        "; raps config profile import ./tmp/raps-staging-export.json --overwrite"
        "; Remove-Item -Force ./tmp/raps-staging-export.json",
        sr_id="SR-038",
        slug="config-profile-import",
    )


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


# ── Snapshot ──────────────────────────────────────────────────────


@pytest.mark.sr("SR-046")
@pytest.mark.require_2leg
def test_sr046_snapshot_create(raps):
    raps.run(
        f"raps snapshot create {SNAP_BUCKET}",
        sr_id="SR-046",
        slug="snapshot-create",
    )


@pytest.mark.sr("SR-049")
@pytest.mark.require_2leg
@pytest.mark.lifecycle
def test_sr049_snapshot_lifecycle(raps):
    lc = raps.lifecycle("SR-049", "snapshot-lifecycle", "Create → list → diff")
    lc.step(f"raps bucket create -k {SNAP_BUCKET} -p transient -r US")
    lc.step(f"raps snapshot create {SNAP_BUCKET} --out-file ./snap-v1.json")
    lc.step("raps snapshot list")
    lc.step(f"raps snapshot create {SNAP_BUCKET} --out-file ./snap-v2.json")
    lc.step("raps snapshot diff ./snap-v1.json ./snap-v2.json")
    lc.step(f"raps bucket delete {SNAP_BUCKET} -y")
    lc.assert_all_passed()
