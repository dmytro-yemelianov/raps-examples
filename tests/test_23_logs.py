"""Log management"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("23-logs"),
]


@pytest.mark.sr("SR-317")
@pytest.mark.lifecycle
def test_sr317_logs_lifecycle(raps):
    lc = raps.lifecycle("SR-317", "logs-lifecycle", "Show → clear → path → show")
    lc.step("raps logs show")
    lc.step("raps logs clear -y")
    lc.step("raps logs path")
    lc.step("raps logs show")
    lc.assert_all_passed()
