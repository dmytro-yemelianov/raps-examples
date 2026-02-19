"""Pipelines"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("18-pipelines"),
]


@pytest.mark.sr("SR-270")
def test_sr270_pipeline_sample(raps):
    raps.run_ok(
        "raps pipeline sample -o ./sample-pipeline.yaml",
        sr_id="SR-270",
        slug="pipeline-sample",
    )


@pytest.mark.sr("SR-271")
def test_sr271_pipeline_validate(raps):
    raps.run_ok(
        "raps pipeline validate ./sample-pipeline.yaml",
        sr_id="SR-271",
        slug="pipeline-validate",
    )


@pytest.mark.sr("SR-272")
def test_sr272_pipeline_run(raps):
    raps.run(
        "raps pipeline run ./sample-pipeline.yaml",
        sr_id="SR-272",
        slug="pipeline-run",
        timeout=120,
    )


@pytest.mark.sr("SR-273")
@pytest.mark.lifecycle
def test_sr273_pipeline_author_and_run(raps):
    lc = raps.lifecycle(
        "SR-273", "pipeline-author-and-run", "DevOps creates and runs pipeline"
    )
    lc.step("raps pipeline sample -o ./my-pipeline.yaml")
    lc.step("raps pipeline validate ./my-pipeline.yaml")
    lc.step("raps pipeline run ./my-pipeline.yaml")
    lc.assert_all_passed()
