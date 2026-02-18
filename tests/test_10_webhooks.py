"""Webhooks"""

import json

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("10-webhooks"),
]

# Default event type used for webhook operations
_EVENT = "dm.version.added"


def _get_first_hook_id(raps) -> str:
    """Extract the first hookId from webhook list JSON output."""
    result = raps.run(
        "raps webhook list --output json",
        sr_id="",
        slug="webhook-list-json-helper",
        may_fail=True,
    )
    if result.ok and result.stdout.strip():
        try:
            hooks = json.loads(result.stdout)
            if hooks and isinstance(hooks, list):
                return hooks[0].get("hookId", "")
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
    return ""


# ── Webhook atomics ──────────────────────────────────────────────


@pytest.mark.sr("SR-180")
def test_sr180_webhook_events(raps):
    raps.run("raps webhook events", sr_id="SR-180", slug="webhook-events", may_fail=True)


@pytest.mark.sr("SR-181")
def test_sr181_webhook_create(raps):
    raps.run(
        f'raps webhook create -e "{_EVENT}" -u "https://example.com/raps-test-hook"',
        sr_id="SR-181",
        slug="webhook-create",
        may_fail=True,
    )


@pytest.mark.sr("SR-182")
def test_sr182_webhook_list(raps):
    raps.run("raps webhook list", sr_id="SR-182", slug="webhook-list", may_fail=True)


@pytest.mark.sr("SR-183")
def test_sr183_webhook_get(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-183",
            slug="webhook-get",
            may_fail=True,
        )
        return
    raps.run(
        f'raps webhook get --hook-id {hook_id} -e "{_EVENT}"',
        sr_id="SR-183",
        slug="webhook-get",
        may_fail=True,
    )


@pytest.mark.sr("SR-184")
def test_sr184_webhook_update(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-184",
            slug="webhook-update",
            may_fail=True,
        )
        return
    raps.run(
        f'raps webhook update --hook-id {hook_id} -e "{_EVENT}" --status inactive',
        sr_id="SR-184",
        slug="webhook-update",
        may_fail=True,
    )


@pytest.mark.sr("SR-185")
def test_sr185_webhook_test(raps):
    raps.run(
        'raps webhook test "https://example.com/webhook"',
        sr_id="SR-185",
        slug="webhook-test",
        may_fail=True,
    )


@pytest.mark.sr("SR-186")
def test_sr186_webhook_verify_signature(raps):
    raps.run(
        """raps webhook verify-signature '{"event":"test"}' --signature "abc123" --secret "my-secret" """,
        sr_id="SR-186",
        slug="webhook-verify-signature",
        may_fail=True,
    )


@pytest.mark.sr("SR-187")
def test_sr187_webhook_delete(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-187",
            slug="webhook-delete",
            may_fail=True,
        )
        return
    raps.run(
        f'raps webhook delete {hook_id} -e "{_EVENT}"',
        sr_id="SR-187",
        slug="webhook-delete",
        may_fail=True,
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-188")
@pytest.mark.lifecycle
def test_sr188_webhook_subscription_lifecycle(raps):
    lc = raps.lifecycle(
        "SR-188", "webhook-subscription-lifecycle", "Create -> list -> update -> delete"
    )
    lc.step(
        f'raps webhook create -e "{_EVENT}" -u "https://example.com/raps-lifecycle-hook"',
        may_fail=True,
    )
    lc.step("raps webhook list", may_fail=True)
    # Steps 3 & 4 use inline shell to extract hookId, matching the bash harness
    lc.step(
        "HOOK_ID=$(raps webhook list --output json 2>/dev/null"
        " | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null"
        " || echo '')"
        ' && [ -n "$HOOK_ID" ]'
        f' && raps webhook update --hook-id "$HOOK_ID" -e "{_EVENT}" --status inactive',
        may_fail=True,
    )
    lc.step(
        "HOOK_ID=$(raps webhook list --output json 2>/dev/null"
        " | python3 -c \"import sys,json; hooks=json.load(sys.stdin); print(hooks[0]['hookId'] if hooks else '')\" 2>/dev/null"
        " || echo '')"
        ' && [ -n "$HOOK_ID" ]'
        f' && raps webhook delete "$HOOK_ID" -e "{_EVENT}"',
        may_fail=True,
    )
    lc.assert_all_passed()
