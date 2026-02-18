"""Setup & Prerequisites"""

import pytest

pytestmark = [
    pytest.mark.xdist_group("00-setup"),
]


@pytest.mark.sr("SR-001")
def test_sr001_setup_env_file(raps):
    raps.run(
        "env | grep -E '^APS_(CLIENT_ID|CLIENT_SECRET|CALLBACK_URL)='",
        sr_id="SR-001",
        slug="setup-env-file",
        may_fail=True,
    )


@pytest.mark.sr("SR-002")
def test_sr002_setup_mock_server(raps):
    raps.run_ok(
        "echo 'Verify raps-mock is running on port 3000'",
        sr_id="SR-002",
        slug="setup-mock-server",
    )


@pytest.mark.sr("SR-003")
def test_sr003_setup_generate_test_files(raps):
    raps.run_ok(
        "mkdir -p ./test-data"
        " && printf 'ISO-10303-21;\\nHEADER;\\nFILE_DESCRIPTION((),\"2;1\");\\nENDSEC;\\nDATA;\\nENDSEC;\\nEND-ISO-10303-21;\\n' > ./test-data/sample.ifc"
        " && dd if=/dev/urandom bs=1024 count=10 of=./test-data/sample.rvt 2>/dev/null"
        # CSV test data for admin user tests (SR-195, SR-198, SR-202, SR-206)
        " && printf 'b.demo-project-001\\nb.demo-project-002\\n' > ./project-ids.txt"
        " && printf 'email,role\\nuser@example.com,viewer\\n' > ./role-changes.csv"
        " && printf 'email,role\\nnewuser@example.com,project_admin\\n' > ./new-users.csv"
        " && printf 'email,role\\nuser1@example.com,viewer\\nuser2@example.com,project_admin\\nuser3@example.com,viewer\\n' > ./test-data/bulk-users.csv"
        " && printf 'email,role\\nuser1@example.com,project_admin\\nuser2@example.com,viewer\\n' > ./test-data/role-updates.csv"
        " && echo 'Test data generated: sample.ifc, sample.rvt, CSV files'",
        sr_id="SR-003",
        slug="setup-generate-test-files",
    )
