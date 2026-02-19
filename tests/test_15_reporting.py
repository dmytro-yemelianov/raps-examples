"""Portfolio Reports"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("15-reporting"),
]


@pytest.mark.sr("SR-240")
def test_sr240_report_rfi_summary(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps report rfi-summary -a {account_id} -f "name:*Tower*" --status open --since "2026-01-01"',
        sr_id="SR-240",
        slug="report-rfi-summary",
    )


@pytest.mark.sr("SR-241")
def test_sr241_report_issues_summary(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps report issues-summary -a {account_id} -f "name:*Phase 2*" --status open',
        sr_id="SR-241",
        slug="report-issues-summary",
    )


@pytest.mark.sr("SR-242")
def test_sr242_report_submittals_summary(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f"raps report submittals-summary -a {account_id}",
        sr_id="SR-242",
        slug="report-submittals-summary",
    )


@pytest.mark.sr("SR-243")
def test_sr243_report_checklists_summary(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps report checklists-summary -a {account_id} --status "in_progress"',
        sr_id="SR-243",
        slug="report-checklists-summary",
    )


@pytest.mark.sr("SR-244")
def test_sr244_report_assets_summary(raps, ids):
    account_id = ids.account_id or "demo-account-001"
    raps.run(
        f'raps report assets-summary -a {account_id} -f "name:*Hospital*"',
        sr_id="SR-244",
        slug="report-assets-summary",
    )
