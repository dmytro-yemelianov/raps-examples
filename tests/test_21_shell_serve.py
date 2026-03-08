"""Shell, Serve, Completions"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("21-shell-serve"),
]


@pytest.mark.sr("SR-301")
def test_sr301_serve_mcp(raps):
    raps.run(
        "Start-Job { raps serve } | Out-Null; Start-Sleep 3; Get-Job | Stop-Job -PassThru | Remove-Job",
        sr_id="SR-301",
        slug="serve-mcp",
    )
