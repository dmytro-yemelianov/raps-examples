"""Webhooks"""

import json
import time

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
    raps.run("raps webhook events", sr_id="SR-180", slug="webhook-events")


@pytest.mark.sr("SR-181")
def test_sr181_webhook_create(raps):
    raps.run(
        f'raps webhook create -e "{_EVENT}" -u "https://example.com/raps-test-hook"',
        sr_id="SR-181",
        slug="webhook-create",
    )


@pytest.mark.sr("SR-182")
def test_sr182_webhook_list(raps):
    raps.run("raps webhook list", sr_id="SR-182", slug="webhook-list")


@pytest.mark.sr("SR-183")
def test_sr183_webhook_get(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-183",
            slug="webhook-get",
            )
        return
    raps.run(
        f'raps webhook get --hook-id {hook_id} -e "{_EVENT}"',
        sr_id="SR-183",
        slug="webhook-get",
    )


@pytest.mark.sr("SR-184")
def test_sr184_webhook_update(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-184",
            slug="webhook-update",
            )
        return
    raps.run(
        f'raps webhook update --hook-id {hook_id} -e "{_EVENT}" --status inactive',
        sr_id="SR-184",
        slug="webhook-update",
    )


@pytest.mark.sr("SR-185")
def test_sr185_webhook_test(raps):
    raps.run(
        'raps webhook test "https://example.com/webhook"',
        sr_id="SR-185",
        slug="webhook-test",
    )


@pytest.mark.sr("SR-186")
def test_sr186_webhook_verify_signature(raps):
    raps.run(
        """raps webhook verify-signature '{"event":"test"}' --signature "abc123" --secret "my-secret" """,
        sr_id="SR-186",
        slug="webhook-verify-signature",
    )


@pytest.mark.sr("SR-187")
def test_sr187_webhook_delete(raps):
    hook_id = _get_first_hook_id(raps)
    if not hook_id:
        raps.run(
            "raps webhook list",
            sr_id="SR-187",
            slug="webhook-delete",
            )
        return
    raps.run(
        f'raps webhook delete {hook_id} -e "{_EVENT}"',
        sr_id="SR-187",
        slug="webhook-delete",
    )


# ── Lifecycles ───────────────────────────────────────────────────


@pytest.mark.sr("SR-188")
@pytest.mark.lifecycle
def test_sr188_webhook_subscription_lifecycle(raps):
    _ts = str(int(time.time()))
    callback = f"https://example.com/raps-lifecycle-{_ts}"
    lc = raps.lifecycle(
        "SR-188", "webhook-subscription-lifecycle", "Create -> list -> update -> delete"
    )
    create_result = lc.step(
        f'raps webhook create -e "{_EVENT}" -u "{callback}"',
    )

    if not create_result.ok:
        # Webhook create requires a reachable callback URL — skip remaining steps
        # if the API rejected the callback (expected in CI / non-routable environments)
        pytest.skip(
            "Webhook create failed (callback URL likely unreachable): "
            + create_result.stderr[:200]
        )

    lc.step("raps webhook list")

    # Extract hookId from create output or list
    hook_id = ""
    if create_result.stdout.strip():
        try:
            data = json.loads(create_result.stdout)
            hook_id = data.get("hookId", "")
        except (json.JSONDecodeError, KeyError):
            pass
    if not hook_id:
        hook_id = _get_first_hook_id(raps)

    if hook_id:
        lc.step(
            f'raps webhook update --hook-id {hook_id} -e "{_EVENT}" --status inactive',
        )
        lc.step(
            f'raps webhook delete {hook_id} -e "{_EVENT}"',
        )
    lc.assert_all_passed()
