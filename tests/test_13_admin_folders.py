"""Admin: Folder Permissions & Operations"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("13-admin-folders"),
]

OPERATION_ID = "12345678-1234-1234-1234-123456789012"
OP_ID = "12345678-1234-1234-1234-123456789012"
OP2_ID = "12345678-1234-1234-1234-123456789013"


# -- Atomic commands --------------------------------------------------------


@pytest.mark.sr("SR-220")
def test_sr220_admin_folder_rights_dryrun(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin folder rights {users.user} -a {account_id}"
        f' -l view-download-upload --folder "Plans" -f "name:*Tower*" --dry-run',
        sr_id="SR-220",
        slug="admin-folder-rights-dryrun",
        may_fail=True,
    )


@pytest.mark.sr("SR-221")
def test_sr221_admin_folder_rights_execute(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin folder rights {users.user} -a {account_id}"
        f' -l view-download-upload --folder "Plans" -f "name:*Tower*" -y',
        sr_id="SR-221",
        slug="admin-folder-rights-execute",
        may_fail=True,
    )


@pytest.mark.sr("SR-222")
def test_sr222_admin_folder_rights_from_file(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin folder rights {users.user} -a {account_id}"
        f" -l folder-control --project-ids ./projects.txt -y",
        sr_id="SR-222",
        slug="admin-folder-rights-from-file",
        may_fail=True,
    )


@pytest.mark.sr("SR-223")
def test_sr223_admin_company_list(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps admin company-list -a {account_id}",
        sr_id="SR-223",
        slug="admin-company-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-224")
def test_sr224_admin_operation_list(raps):
    raps.run(
        "raps admin operation list --status completed --limit 5",
        sr_id="SR-224",
        slug="admin-operation-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-225")
def test_sr225_admin_operation_status(raps):
    raps.run(
        f"raps admin operation status {OPERATION_ID}",
        sr_id="SR-225",
        slug="admin-operation-status",
        may_fail=True,
    )


@pytest.mark.sr("SR-226")
def test_sr226_admin_operation_resume(raps):
    raps.run(
        f"raps admin operation resume {OPERATION_ID} --concurrency 3",
        sr_id="SR-226",
        slug="admin-operation-resume",
        may_fail=True,
    )


@pytest.mark.sr("SR-227")
def test_sr227_admin_operation_cancel(raps):
    raps.run(
        f"raps admin operation cancel {OPERATION_ID} -y",
        sr_id="SR-227",
        slug="admin-operation-cancel",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-228")
@pytest.mark.lifecycle
def test_sr228_folder_permissions_lifecycle(raps, ids, users):
    account_id = ids.account_id or "demo-account-001"
    lc = raps.lifecycle(
        "SR-228", "folder-permissions-lifecycle", "Grant, verify, restrict folder access"
    )
    lc.step(
        f"raps admin folder rights {users.user_folder} -a {account_id}"
        f' -l view-download-upload-edit --folder "Plans" -f "name:*Active*" --dry-run',
        may_fail=True,
    )
    lc.step(
        f"raps admin folder rights {users.user_folder} -a {account_id}"
        f' -l view-download-upload-edit --folder "Plans" -f "name:*Active*" -y',
        may_fail=True,
    )
    lc.step("raps admin operation list --limit 1", may_fail=True)
    lc.step(f"raps admin operation status {OP_ID}", may_fail=True)
    lc.step(
        f"raps admin folder rights {users.user_folder} -a {account_id}"
        f' -l view-only --folder "Plans" -f "name:*Active*" -y',
        may_fail=True,
    )
    lc.step(f"raps admin operation status {OP2_ID}", may_fail=True)
    lc.assert_all_passed()
