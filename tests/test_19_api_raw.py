"""Raw API"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("19-api-raw"),
]


@pytest.mark.sr("SR-280")
def test_sr280_api_get(raps):
    raps.run(
        "raps api get /oss/v2/buckets",
        sr_id="SR-280",
        slug="api-get",
    )


@pytest.mark.sr("SR-281")
def test_sr281_api_post(raps):
    raps.run(
        "raps api post \"/oss/v2/buckets\""
        " -d '{\"bucketKey\":\"api-raw-test-raps\",\"policyKey\":\"transient\"}'",
        sr_id="SR-281",
        slug="api-post",
    )


@pytest.mark.sr("SR-282")
def test_sr282_api_put(raps):
    raps.run(
        "raps api put"
        " \"/webhooks/v1/systems/data/events/dm.version.added/hooks/dummy-hook-id\""
        " -d '{\"status\":\"inactive\"}'",
        sr_id="SR-282",
        slug="api-put",
    )


@pytest.mark.sr("SR-283")
def test_sr283_api_patch(raps):
    raps.run(
        "raps api patch"
        " \"/construction/issues/v1/projects/dummy-project/issues/dummy-issue\""
        " -d '{\"title\":\"updated\"}'",
        sr_id="SR-283",
        slug="api-patch",
    )


@pytest.mark.sr("SR-284")
def test_sr284_api_delete(raps):
    raps.run(
        "raps api delete"
        " \"/oss/v2/buckets/api-raw-nonexistent-bucket\"",
        sr_id="SR-284",
        slug="api-delete",
    )
