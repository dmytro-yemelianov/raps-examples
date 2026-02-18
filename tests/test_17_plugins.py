"""Plugins"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("17-plugins"),
]


@pytest.mark.sr("SR-260")
def test_sr260_plugin_list(raps):
    raps.run_ok("raps plugin list", sr_id="SR-260", slug="plugin-list")


@pytest.mark.sr("SR-261")
def test_sr261_plugin_enable(raps):
    raps.run_ok("raps plugin enable my-plugin", sr_id="SR-261", slug="plugin-enable")


@pytest.mark.sr("SR-262")
def test_sr262_plugin_disable(raps):
    raps.run_ok(
        "raps plugin disable my-plugin", sr_id="SR-262", slug="plugin-disable"
    )


@pytest.mark.sr("SR-263")
def test_sr263_plugin_alias_list(raps):
    raps.run_ok("raps plugin alias list", sr_id="SR-263", slug="plugin-alias-list")


@pytest.mark.sr("SR-264")
def test_sr264_plugin_alias_add(raps):
    raps.run_ok(
        'raps plugin alias add "bl" "bucket list"',
        sr_id="SR-264",
        slug="plugin-alias-add",
    )


@pytest.mark.sr("SR-265")
def test_sr265_plugin_alias_remove(raps):
    raps.run_ok(
        'raps plugin alias remove "bl"',
        sr_id="SR-265",
        slug="plugin-alias-remove",
    )


@pytest.mark.sr("SR-266")
@pytest.mark.lifecycle
def test_sr266_alias_power_user_lifecycle(raps):
    lc = raps.lifecycle("SR-266", "alias-power-user-lifecycle", "Developer sets up aliases")
    lc.step('raps plugin alias add "bl" "bucket list"')
    lc.step('raps plugin alias add "ol" "object list"')
    lc.step('raps plugin alias add "ts" "translate status"')
    lc.step("raps plugin alias list")
    lc.step("raps plugin alias list | grep bl", may_fail=True)
    lc.step('raps plugin alias remove "bl"')
    lc.step("raps plugin alias list")
    lc.assert_all_passed()
