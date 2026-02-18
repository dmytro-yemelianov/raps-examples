"""Templates"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("16-templates"),
]

TEMPLATE_ID = "tpl-demo-001"
TPL_ID = "tpl-demo-001"


# -- Atomic commands --------------------------------------------------------


@pytest.mark.sr("SR-250")
def test_sr250_template_list(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps template list -a {account_id}",
        sr_id="SR-250",
        slug="template-list",
        may_fail=True,
    )


@pytest.mark.sr("SR-251")
def test_sr251_template_create(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps template create -a {account_id} --name "Standard Building Template"',
        sr_id="SR-251",
        slug="template-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-252")
def test_sr252_template_info(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps template info {TEMPLATE_ID} -a {account_id}",
        sr_id="SR-252",
        slug="template-info",
        may_fail=True,
    )


@pytest.mark.sr("SR-253")
def test_sr253_template_update(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps template update {TEMPLATE_ID} -a {account_id} --name "Standard Building Template v2"',
        sr_id="SR-253",
        slug="template-update",
        may_fail=True,
    )


@pytest.mark.sr("SR-254")
def test_sr254_template_archive(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps template archive {TEMPLATE_ID} -a {account_id}",
        sr_id="SR-254",
        slug="template-archive",
        may_fail=True,
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-255")
@pytest.mark.lifecycle
@pytest.mark.require_acc
def test_sr255_template_management_lifecycle(raps, ids):
    import json
    import time

    account_id = ids.account_id or "demo-account-001"
    name = f"Healthcare Template {int(time.time())}"
    lc = raps.lifecycle("SR-255", "template-management-lifecycle", "Admin manages templates")
    result = lc.step(
        f'raps template create -a {account_id} --name "{name}" --output json',
        may_fail=True,
    )
    tpl_id = "tpl-demo-001"
    if result.ok:
        try:
            tpl_id = json.loads(result.stdout).get("id", tpl_id)
        except (json.JSONDecodeError, KeyError):
            pass
    lc.step(f"raps template list -a {account_id}", may_fail=True)
    lc.step(f"raps template info {tpl_id} -a {account_id}", may_fail=True)
    lc.step(f'raps template update {tpl_id} -a {account_id} --name "Healthcare Template 2026"', may_fail=True)
    lc.step(f"raps template archive {tpl_id} -a {account_id}", may_fail=True)
    lc.step(f"raps template list -a {account_id}", may_fail=True)
    lc.assert_all_passed()
