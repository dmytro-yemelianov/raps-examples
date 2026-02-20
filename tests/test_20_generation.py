"""Generation"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("20-generation"),
]


@pytest.mark.sr("SR-290")
def test_sr290_generate_files_simple(raps):
    raps.run_ok(
        "raps generate files -c 1 --out-dir ./gen-simple/ --complexity simple",
        sr_id="SR-290",
        slug="generate-files-simple",
    )


@pytest.mark.sr("SR-291")
def test_sr291_generate_files_complex(raps):
    raps.run_ok(
        "raps generate files -c 10 --out-dir ./gen-complex/ --complexity complex",
        sr_id="SR-291",
        slug="generate-files-complex",
    )
