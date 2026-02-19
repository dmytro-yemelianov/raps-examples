"""Cross-Cutting"""

import pytest

pytestmark = [
    pytest.mark.require_2leg,
    pytest.mark.xdist_group("99-cross-cutting"),
]


# ── Output format matrix: bucket list ────────────────────────────


@pytest.mark.parametrize(
    "fmt,sr_id",
    [
        ("table", "SR-500"),
        ("json", "SR-501"),
        ("yaml", "SR-502"),
        ("csv", "SR-503"),
        ("plain", "SR-504"),
    ],
)
def test_bucket_list_output_format(raps, fmt, sr_id):
    raps.run(
        f"raps bucket list --output {fmt}",
        sr_id=sr_id,
        slug=f"bucket-list-{fmt}",
    )


# ── Output format matrix: issue list (requires 3-legged auth) ────


@pytest.mark.require_3leg
@pytest.mark.parametrize(
    "fmt,sr_id",
    [
        ("table", "SR-505"),
        ("json", "SR-506"),
        ("yaml", "SR-507"),
        ("csv", "SR-508"),
        ("plain", "SR-509"),
    ],
)
def test_issue_list_output_format(raps, ids, fmt, sr_id):
    raps.run(
        f"raps issue list {ids.project_id} --output {fmt}",
        sr_id=sr_id,
        slug=f"issue-list-{fmt}",
    )


# ── Output format matrix: admin user list (requires 3-legged auth) ──


@pytest.mark.require_3leg
@pytest.mark.parametrize(
    "fmt,sr_id",
    [
        ("table", "SR-510"),
        ("json", "SR-511"),
        ("yaml", "SR-512"),
        ("csv", "SR-513"),
        ("plain", "SR-514"),
    ],
)
def test_admin_user_list_output_format(raps, ids, fmt, sr_id):
    raps.run(
        f"raps admin user list -a {ids.account_id} --output {fmt}",
        sr_id=sr_id,
        slug=f"admin-user-list-{fmt}",
    )


# ── Output format matrix: hub list (requires 3-legged auth) ─────


@pytest.mark.require_3leg
@pytest.mark.parametrize(
    "fmt,sr_id",
    [
        ("table", "SR-515"),
        ("json", "SR-516"),
        ("yaml", "SR-517"),
        ("csv", "SR-518"),
        ("plain", "SR-519"),
    ],
)
def test_hub_list_output_format(raps, fmt, sr_id):
    raps.run(
        f"raps hub list --output {fmt}",
        sr_id=sr_id,
        slug=f"hub-list-{fmt}",
    )


# ── Output format matrix: DA engines ─────────────────────────────


@pytest.mark.parametrize(
    "fmt,sr_id",
    [
        ("table", "SR-520"),
        ("json", "SR-521"),
        ("yaml", "SR-522"),
        ("csv", "SR-523"),
        ("plain", "SR-524"),
    ],
)
def test_da_engines_output_format(raps, fmt, sr_id):
    raps.run(
        f"raps da engines --output {fmt}",
        sr_id=sr_id,
        slug=f"da-engines-{fmt}",
    )


# ── No-color ─────────────────────────────────────────────────────


@pytest.mark.sr("SR-530")
def test_sr530_no_color_bucket_list(raps):
    raps.run(
        "raps bucket list --no-color",
        sr_id="SR-530",
        slug="no-color-bucket-list",
    )


@pytest.mark.sr("SR-531")
@pytest.mark.require_3leg
def test_sr531_no_color_issue_list(raps, ids):
    raps.run(
        f"raps issue list {ids.project_id} --no-color",
        sr_id="SR-531",
        slug="no-color-issue-list",
    )


# ── Help & version ───────────────────────────────────────────────


@pytest.mark.sr("SR-540")
def test_sr540_help_top_level(raps):
    raps.run_ok("raps --help", sr_id="SR-540", slug="help-top-level")


@pytest.mark.sr("SR-541")
def test_sr541_help_auth(raps):
    raps.run_ok("raps auth --help", sr_id="SR-541", slug="help-auth")


@pytest.mark.sr("SR-542")
def test_sr542_help_admin(raps):
    raps.run_ok("raps admin --help", sr_id="SR-542", slug="help-admin")


@pytest.mark.sr("SR-543")
def test_sr543_help_admin_user(raps):
    raps.run_ok("raps admin user --help", sr_id="SR-543", slug="help-admin-user")


@pytest.mark.sr("SR-544")
def test_sr544_help_version(raps):
    raps.run_ok("raps --version", sr_id="SR-544", slug="help-version")
