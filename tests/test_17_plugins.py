"""Plugins"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("17-plugins"),
]


@pytest.mark.sr("SR-266")
@pytest.mark.lifecycle
def test_sr266_alias_power_user_lifecycle(raps):
    lc = raps.lifecycle("SR-266", "alias-power-user-lifecycle", "Developer sets up aliases")
    lc.step('raps plugin alias add "bl" "bucket list"')
    lc.step('raps plugin alias add "ol" "object list"')
    lc.step('raps plugin alias add "ts" "translate status"')
    lc.step("raps plugin alias list")
    lc.step("raps plugin alias list | grep bl")
    lc.step('raps plugin alias remove "bl"')
    lc.step("raps plugin alias list")
    lc.assert_all_passed()
