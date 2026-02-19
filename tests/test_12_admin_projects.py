"""Admin: Project Management"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("12-admin-projects"),
]


# -- Atomic commands --------------------------------------------------------


@pytest.mark.sr("SR-210")
def test_sr210_admin_project_list(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin project list -a {account_id}",
        sr_id="SR-210",
        slug="admin-project-list",
    )


@pytest.mark.sr("SR-211")
def test_sr211_admin_project_list_filtered(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin project list -a {account_id} -f "name:*Tower*"'
        f" --status active --platform acc --limit 10",
        sr_id="SR-211",
        slug="admin-project-list-filtered",
    )


@pytest.mark.sr("SR-212")
def test_sr212_admin_project_create(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin project create -a {account_id} --name "Tower Phase 3" -t "Bridge"'
        f' --classification "Sample" --start-date "2026-03-01" --end-date "2027-12-31"'
        f' --timezone "America/New_York"',
        sr_id="SR-212",
        slug="admin-project-create",
    )


@pytest.mark.sr("SR-213")
def test_sr213_admin_project_update(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps admin project update -a {account_id} -p {project_id}'
        f' --name "Tower Phase 3 - Revised" --status active',
        sr_id="SR-213",
        slug="admin-project-update",
    )


@pytest.mark.sr("SR-214")
def test_sr214_admin_project_archive(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps admin project archive -a {account_id} -p {project_id}",
        sr_id="SR-214",
        slug="admin-project-archive",
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-215")
@pytest.mark.lifecycle
@pytest.mark.require_acc
def test_sr215_project_lifecycle_admin(raps, ids, users):
    import json
    import time

    account_id = ids.account_id or "demo-account-001"
    name = f"Bridge Retrofit {int(time.time())}"
    lc = raps.lifecycle("SR-215", "project-lifecycle-admin", "Create and manage project")
    result = lc.step(
        f'raps admin project create -a {account_id} --name "{name}" -t "Bridge" --output json',
    )
    pid = ids.project_id or "demo-project-001"
    if result.ok:
        try:
            pid = json.loads(result.stdout).get("id", pid)
        except (json.JSONDecodeError, KeyError):
            pass
    lc.step(f'raps admin project list -a {account_id} -f "name:*Bridge*"')
    lc.step(
        f'raps admin user add {users.user_pm} -a {account_id}'
        f' -r "project_admin" -f "name:*Bridge Retrofit*" -y',
    )
    lc.step(f'raps admin project update -a {account_id} -p {pid} --start-date "2026-04-01"')
    lc.step(f"raps admin project archive -a {account_id} -p {pid}")
    lc.step(f"raps admin project list -a {account_id} --status active")
    lc.assert_all_passed()
