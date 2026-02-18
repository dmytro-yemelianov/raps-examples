"""Admin: Bulk User Management"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("11-admin-users"),
]

ROLE_ID = "role-demo-001"
NEW_ROLE_ID = "role-demo-002"
OLD_PROJECT = "b.demo-old-project-001"


# -- Atomic commands --------------------------------------------------------


@pytest.mark.sr("SR-190")
def test_sr190_admin_user_list_account(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin user list -a {account_id}",
        sr_id="SR-190",
        slug="admin-user-list-account",
        may_fail=True,
    )


@pytest.mark.sr("SR-191")
def test_sr191_admin_user_list_project(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps admin user list -a {account_id} -p {project_id}",
        sr_id="SR-191",
        slug="admin-user-list-project",
        may_fail=True,
    )


@pytest.mark.sr("SR-192")
def test_sr192_admin_user_list_filtered(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user list -a {account_id} --role "project_admin" --status "active" --search "john"',
        sr_id="SR-192",
        slug="admin-user-list-filtered",
        may_fail=True,
    )


@pytest.mark.sr("SR-193")
def test_sr193_admin_user_add_bulk_dryrun(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user add {users.user} -a {account_id} -r "project_admin"'
        f' -f "name:*Tower*" --dry-run',
        sr_id="SR-193",
        slug="admin-user-add-bulk-dryrun",
        may_fail=True,
    )


@pytest.mark.sr("SR-194")
def test_sr194_admin_user_add_bulk_execute(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user add {users.user} -a {account_id} -r "project_admin"'
        f' -f "name:*Tower*" -y',
        sr_id="SR-194",
        slug="admin-user-add-bulk-execute",
        may_fail=True,
    )


@pytest.mark.sr("SR-195")
def test_sr195_admin_user_add_from_file(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user add {users.user} -a {account_id} -r "viewer"'
        f" --project-ids ./project-ids.txt -y",
        sr_id="SR-195",
        slug="admin-user-add-from-file",
        may_fail=True,
    )


@pytest.mark.sr("SR-196")
def test_sr196_admin_user_remove_bulk_dryrun(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user remove {users.user} -a {account_id} -f "name:*Old Project*" --dry-run',
        sr_id="SR-196",
        slug="admin-user-remove-bulk-dryrun",
        may_fail=True,
    )


@pytest.mark.sr("SR-197")
def test_sr197_admin_user_update_bulk_dryrun(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps admin user update {users.user} -a {account_id} -r "viewer"'
        f' --from-role "project_admin" -f "name:*Archive*" --dry-run',
        sr_id="SR-197",
        slug="admin-user-update-bulk-dryrun",
        may_fail=True,
    )


@pytest.mark.sr("SR-198")
def test_sr198_admin_user_update_from_csv(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin user update {users.user} -a {account_id}"
        f" --from-csv ./role-changes.csv -y",
        sr_id="SR-198",
        slug="admin-user-update-from-csv",
        may_fail=True,
    )


@pytest.mark.sr("SR-199")
def test_sr199_admin_user_add_single(raps, ids, users):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps admin user add-to-project -p {project_id} -e "{users.user_add}" -r {ROLE_ID}',
        sr_id="SR-199",
        slug="admin-user-add-single",
        may_fail=True,
    )


@pytest.mark.sr("SR-200")
def test_sr200_admin_user_update_single(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    user_id = ids.user_id or "demo-user-001"
    raps.run(
        f"raps admin user update-in-project -p {project_id} -u {user_id} -r {NEW_ROLE_ID}",
        sr_id="SR-200",
        slug="admin-user-update-single",
        may_fail=True,
    )


@pytest.mark.sr("SR-201")
def test_sr201_admin_user_remove_single(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    user_id = ids.user_id or "demo-user-001"
    raps.run(
        f"raps admin user remove-from-project -p {project_id} -u {user_id} -y",
        sr_id="SR-201",
        slug="admin-user-remove-single",
        may_fail=True,
    )


@pytest.mark.sr("SR-202")
def test_sr202_admin_user_import_csv(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps admin user import -p {project_id} --from-csv ./new-users.csv",
        sr_id="SR-202",
        slug="admin-user-import-csv",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-203")
@pytest.mark.lifecycle
def test_sr203_new_employee_onboarding(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-203", "new-employee-onboarding", "Account admin onboards new team member")
    lc.step(f'raps admin user list -a {account_id} --search "{users.user_new}"', may_fail=True)
    lc.step(f'raps admin project list -a {account_id} --status active -f "name:*Building*"', may_fail=True)
    lc.step(
        f'raps admin user add {users.user_new} -a {account_id} -r "project_admin"'
        f' -f "name:*Building*" --dry-run',
        may_fail=True,
    )
    lc.step(
        f'raps admin user add {users.user_new} -a {account_id} -r "project_admin"'
        f' -f "name:*Building*" -y',
        may_fail=True,
    )
    lc.step(f'raps admin user list -a {account_id} --search "{users.user_new}"', may_fail=True)
    lc.step(
        f"raps admin folder rights {users.user_new} -a {account_id}"
        f' -l view-download-upload --folder "Plans" -f "name:*Building*" --dry-run',
        may_fail=True,
    )
    lc.step(
        f"raps admin folder rights {users.user_new} -a {account_id}"
        f' -l view-download-upload --folder "Plans" -f "name:*Building*" -y',
        may_fail=True,
    )
    lc.assert_all_passed()


@pytest.mark.sr("SR-204")
@pytest.mark.lifecycle
def test_sr204_employee_offboarding(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-204", "employee-offboarding", "Remove departing employee")
    lc.step(f'raps admin user list -a {account_id} --search "{users.user_departing}"', may_fail=True)
    lc.step(f"raps admin user remove {users.user_departing} -a {account_id} --dry-run", may_fail=True)
    lc.step(f"raps admin user remove {users.user_departing} -a {account_id} -y", may_fail=True)
    lc.step(f'raps admin user list -a {account_id} --search "{users.user_departing}"', may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-205")
@pytest.mark.lifecycle
def test_sr205_role_migration(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    lc = raps.lifecycle("SR-205", "role-migration", "Downgrade stale admins to viewers")
    lc.step(f'raps admin project list -a {account_id} --status active -f "name:*2024*"', may_fail=True)
    lc.step(f'raps admin user list -a {account_id} --role "project_admin"', may_fail=True)
    lc.step(
        f'raps admin user update {users.user_admin} -a {account_id} -r "viewer"'
        f' --from-role "project_admin" -f "name:*2024*" --dry-run',
        may_fail=True,
    )
    lc.step(
        f'raps admin user update {users.user_admin} -a {account_id} -r "viewer"'
        f' --from-role "project_admin" -f "name:*2024*" -y',
        may_fail=True,
    )
    lc.step(f'raps admin user list -a {account_id} -p {OLD_PROJECT} --role "project_admin"', may_fail=True)
    lc.assert_all_passed()


@pytest.mark.sr("SR-206")
@pytest.mark.lifecycle
def test_sr206_csv_batch_onboarding(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    project_id = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-206", "csv-batch-onboarding", "Onboard 50 users from CSV")
    lc.step(f"raps admin user import -p {project_id} --from-csv ./test-data/bulk-users.csv", may_fail=True)
    lc.step(f"raps admin user list -a {account_id} -p {project_id}", may_fail=True)
    lc.step(
        f"raps admin user update {users.user_csv} -a {account_id}"
        f" --from-csv ./test-data/role-updates.csv -y",
        may_fail=True,
    )
    lc.step(f'raps admin user list -a {account_id} -p {project_id} --role "project_admin"', may_fail=True)
    lc.assert_all_passed()
