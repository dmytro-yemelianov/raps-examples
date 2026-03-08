"""Log management"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("23-logs"),
]


@pytest.mark.sr("SR-310")
def test_sr310_logs_path(raps):
    raps.run_ok("raps logs path", sr_id="SR-310", slug="logs-path")


@pytest.mark.sr("SR-311")
def test_sr311_logs_show(raps):
    raps.run_ok("raps logs show", sr_id="SR-311", slug="logs-show")


@pytest.mark.sr("SR-312")
def test_sr312_logs_clear(raps):
    raps.run_ok("raps logs clear -y", sr_id="SR-312", slug="logs-clear")


@pytest.mark.sr("SR-313")
@pytest.mark.lifecycle
def test_sr313_logs_lifecycle(raps):
    lc = raps.lifecycle("SR-313", "logs-lifecycle", "Clear → show → path")
    lc.step("raps logs clear -y")
    lc.step("raps logs show")
    lc.step("raps logs path")
    lc.assert_all_passed()
