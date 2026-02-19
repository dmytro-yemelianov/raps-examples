"""Demo"""

from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.xdist_group("22-demo"),
]


@pytest.mark.sr("SR-310")
def test_sr310_demo_bucket_lifecycle(raps):
    raps.run(
        "raps demo bucket-lifecycle --non-interactive",
        sr_id="SR-310",
        slug="demo-bucket-lifecycle",
        timeout=120,
    )


@pytest.mark.sr("SR-311")
def test_sr311_demo_model_pipeline(raps):
    if not Path("./test-data/sample.rvt").is_file():
        pytest.skip("missing ./test-data/sample.rvt")
    raps.run(
        "raps demo model-pipeline --file ./test-data/sample.rvt --non-interactive",
        sr_id="SR-311",
        slug="demo-model-pipeline",
        timeout=120,
    )


@pytest.mark.sr("SR-312")
def test_sr312_demo_data_management(raps):
    raps.run(
        "raps demo data-management --non-interactive --export ./dm-report.json",
        sr_id="SR-312",
        slug="demo-data-management",
    )


@pytest.mark.sr("SR-313")
def test_sr313_demo_batch_processing(raps):
    if not Path("./test-data").is_dir():
        pytest.skip("missing ./test-data/")
    raps.run(
        "raps demo batch-processing --input ./test-data/ --non-interactive",
        sr_id="SR-313",
        slug="demo-batch-processing",
        timeout=120,
    )
