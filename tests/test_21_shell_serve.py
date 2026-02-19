"""Shell, Serve, Completions"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("21-shell-serve"),
]


@pytest.mark.sr("SR-300")
def test_sr300_shell_interactive(raps):
    raps.run(
        'echo "exit" | raps shell',
        sr_id="SR-300",
        slug="shell-interactive",
    )


@pytest.mark.sr("SR-301")
def test_sr301_serve_mcp(raps):
    raps.run(
        "Start-Job { raps serve } | Out-Null; Start-Sleep 3; Get-Job | Stop-Job -PassThru | Remove-Job",
        sr_id="SR-301",
        slug="serve-mcp",
    )


@pytest.mark.sr("SR-302")
def test_sr302_completions_bash(raps):
    raps.run_ok("raps completions bash", sr_id="SR-302", slug="completions-bash")


@pytest.mark.sr("SR-303")
def test_sr303_completions_powershell(raps):
    raps.run_ok(
        "raps completions powershell", sr_id="SR-303", slug="completions-powershell"
    )


@pytest.mark.sr("SR-304")
def test_sr304_completions_zsh(raps):
    raps.run_ok("raps completions zsh", sr_id="SR-304", slug="completions-zsh")


@pytest.mark.sr("SR-305")
def test_sr305_completions_fish(raps):
    raps.run_ok("raps completions fish", sr_id="SR-305", slug="completions-fish")


@pytest.mark.sr("SR-306")
def test_sr306_completions_elvish(raps):
    raps.run_ok("raps completions elvish", sr_id="SR-306", slug="completions-elvish")
