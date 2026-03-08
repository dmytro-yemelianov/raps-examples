"""Pipelines"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("18-pipelines"),
]


@pytest.mark.sr("SR-273")
@pytest.mark.lifecycle
def test_sr273_pipeline_author_and_run(raps):
    lc = raps.lifecycle(
        "SR-273", "pipeline-author-and-run", "DevOps creates and runs pipeline"
    )
    lc.step("raps pipeline sample --out-file ./my-pipeline.yaml")
    lc.step("raps pipeline validate ./my-pipeline.yaml")
    lc.step("raps pipeline run ./my-pipeline.yaml --dry-run")
    lc.assert_all_passed()
