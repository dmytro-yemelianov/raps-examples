"""Log management"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("23-logs"),
]


@pytest.mark.sr("SR-314")
def test_sr314_logs_path(raps):
    raps.run_ok("raps logs path", sr_id="SR-314", slug="logs-path")


@pytest.mark.sr("SR-315")
def test_sr315_logs_show(raps):
    raps.run_ok("raps logs show", sr_id="SR-315", slug="logs-show")


@pytest.mark.sr("SR-316")
def test_sr316_logs_clear(raps):
    raps.run_ok("raps logs clear -y", sr_id="SR-316", slug="logs-clear")


@pytest.mark.sr("SR-317")
@pytest.mark.lifecycle
def test_sr317_logs_lifecycle(raps):
    lc = raps.lifecycle("SR-317", "logs-lifecycle", "Show → clear → path → show")
    lc.step("raps logs show")
    lc.step("raps logs clear -y")
    lc.step("raps logs path")
    lc.step("raps logs show")
    lc.assert_all_passed()
