"""Cross-Cutting"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("99-cross-cutting"),
]


# ── --log-file global flag ───────────────────────────────────────


@pytest.mark.sr("SR-560")
def test_sr560_log_file_flag(raps, tmp_path):
    log_file = tmp_path / "raps-test.log"
    raps.run_ok(
        f"raps --log-file {log_file} bucket list",
        sr_id="SR-560",
        slug="log-file-flag",
    )
