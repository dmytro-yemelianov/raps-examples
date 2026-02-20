"""ACC Issues"""

import pytest

pytestmark = [
    pytest.mark.require_3leg,
    pytest.mark.xdist_group("07-acc-issues"),
]

ISSUE_ID = "8d5b8b2c-3a1e-467c-9f1b-6c2d9a8e1f5b"
COMMENT_ID = "cmt-demo-001"
ID = "8d5b8b2c-3a1e-467c-9f1b-6c2d9a8e1f5b"
A = "issue-a-demo-001"
B = "issue-b-demo-002"
C = "issue-c-demo-003"


# -- Issue atomics ----------------------------------------------------------


@pytest.mark.sr("SR-130")
def test_sr130_issue_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue list {project_id}",
        sr_id="SR-130",
        slug="issue-list",
    )


@pytest.mark.sr("SR-131")
def test_sr131_issue_types(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue types {project_id}",
        sr_id="SR-131",
        slug="issue-types",
    )


@pytest.mark.sr("SR-132")
def test_sr132_issue_create(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps issue create {project_id} --title "Cracked concrete on Level 2"'
        f' --description "Visible crack near column C4"',
        sr_id="SR-132",
        slug="issue-create",
    )


@pytest.mark.sr("SR-133")
def test_sr133_issue_update(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps issue update {project_id} {ISSUE_ID} --title "Cracked concrete on Level 2 - URGENT"',
        sr_id="SR-133",
        slug="issue-update",
    )


@pytest.mark.sr("SR-134")
def test_sr134_issue_transition(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps issue transition {project_id} {ISSUE_ID} --to "in_review"',
        sr_id="SR-134",
        slug="issue-transition",
    )


@pytest.mark.sr("SR-135")
def test_sr135_issue_comment_add(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f'raps issue comment add {project_id} {ISSUE_ID} --body "Structural engineer notified"',
        sr_id="SR-135",
        slug="issue-comment-add",
    )


@pytest.mark.sr("SR-136")
def test_sr136_issue_comment_list(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue comment list {project_id} {ISSUE_ID}",
        sr_id="SR-136",
        slug="issue-comment-list",
    )


@pytest.mark.sr("SR-137")
def test_sr137_issue_comment_delete(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue comment delete {project_id} {ISSUE_ID} {COMMENT_ID} --yes",
        sr_id="SR-137",
        slug="issue-comment-delete",
    )


@pytest.mark.sr("SR-138")
def test_sr138_issue_attachments(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue attachments {project_id} {ISSUE_ID}",
        sr_id="SR-138",
        slug="issue-attachments",
    )


@pytest.mark.sr("SR-139")
def test_sr139_issue_delete(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    raps.run(
        f"raps issue delete {project_id} {ISSUE_ID} --yes",
        sr_id="SR-139",
        slug="issue-delete",
    )


# -- Lifecycles -------------------------------------------------------------


@pytest.mark.sr("SR-140")
@pytest.mark.lifecycle
def test_sr140_issue_full_lifecycle(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-140", "issue-full-lifecycle", "Field engineer reports and tracks a defect")
    lc.step(f"raps issue types {project_id}")
    lc.step(f'raps issue create {project_id} --title "Water damage in corridor B"')
    lc.step(f"raps issue list {project_id}")
    lc.step(f'raps issue comment add {project_id} {ID} --body "Photo attached via mobile"')
    lc.step(f"raps issue comment list {project_id} {ID}")
    lc.step(f'raps issue update {project_id} {ID} --title "Water damage in corridor B - assigned"')
    lc.step(f'raps issue transition {project_id} {ID} --to "answered"')
    lc.step(f'raps issue transition {project_id} {ID} --to "closed"')
    lc.step(f"raps issue delete {project_id} {ID} --yes")
    lc.assert_all_passed()


@pytest.mark.sr("SR-141")
@pytest.mark.lifecycle
def test_sr141_issue_triage_workflow(raps, ids):
    project_id = ids.project_id or "demo-project-001"
    lc = raps.lifecycle("SR-141", "issue-triage-workflow", "QA lead triages multiple issues")
    lc.step(f'raps issue create {project_id} --title "Issue A"')
    lc.step(f'raps issue create {project_id} --title "Issue B"')
    lc.step(f'raps issue create {project_id} --title "Issue C"')
    lc.step(f"raps issue list {project_id} --output json")
    lc.step(f'raps issue update {project_id} {A} --title "Issue A - assigned"')
    lc.step(f'raps issue update {project_id} {B} --title "Issue B - assigned"')
    lc.step(f'raps issue transition {project_id} {C} --to "closed"')
    lc.step(f"raps issue list {project_id}")
    lc.assert_all_passed()
