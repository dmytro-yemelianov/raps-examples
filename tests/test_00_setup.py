"""Setup & Prerequisites"""

from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.xdist_group("00-setup"),
]


@pytest.mark.sr("SR-001")
def test_sr001_setup_env_file(raps):
    raps.run(
        "Get-ChildItem Env:APS_*",
        sr_id="SR-001",
        slug="setup-env-file",
    )


@pytest.mark.sr("SR-002")
def test_sr002_setup_mock_server(raps):
    raps.run_ok(
        "echo 'Verify raps-mock is running on port 3000'",
        sr_id="SR-002",
        slug="setup-mock-server",
    )


@pytest.mark.sr("SR-003")
def test_sr003_setup_generate_test_files(raps, test_data):
    """Generate deterministic test fixture files with valid format headers."""
    _generate_ifc(test_data / "sample.ifc")
    _generate_stp(test_data / "sample.stp")
    _generate_rvt(test_data / "sample.rvt")
    _generate_dwg(test_data / "sample.dwg")
    _generate_csvs(test_data)
    _generate_admin_csvs(test_data)

    # Verify all files exist
    expected = ["sample.ifc", "sample.stp", "sample.rvt", "sample.dwg",
                "bulk-users.csv", "role-updates.csv"]
    for fname in expected:
        assert (test_data / fname).is_file(), f"Missing: {fname}"

    raps.run_ok(
        f"echo 'Test data generated: {', '.join(expected)}'",
        sr_id="SR-003",
        slug="setup-generate-test-files",
    )


# ── Fixture generators (deterministic, valid headers) ──────────────


def _generate_ifc(path: Path) -> None:
    """Generate a minimal valid IFC4 file (ISO-10303-21 format)."""
    path.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');\n"
        "FILE_NAME('sample.ifc','2026-01-01T00:00:00',('Test'),('RAPS'),"
        "'RAPS Sample','RAPS','');\n"
        "FILE_SCHEMA(('IFC4'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=IFCPROJECT('0001',#2,'Sample Project',$,$,$,$,$,#3);\n"
        "#2=IFCOWNERHISTORY(#4,#5,$,.NOCHANGE.,$,$,$,0);\n"
        "#3=IFCUNITASSIGNMENT((#6));\n"
        "#4=IFCPERSONANDORGANIZATION(#7,#8,$);\n"
        "#5=IFCAPPLICATION(#8,'1.0','RAPS','RAPS');\n"
        "#6=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);\n"
        "#7=IFCPERSON($,'Test',$,$,$,$,$,$);\n"
        "#8=IFCORGANIZATION($,'RAPS',$,$,$);\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n",
        encoding="utf-8",
    )


def _generate_stp(path: Path) -> None:
    """Generate a minimal valid STEP file (ISO-10303-21, AP214)."""
    path.write_text(
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('STEP AP214'),'2;1');\n"
        "FILE_NAME('sample.stp','2026-01-01T00:00:00',('Test'),('RAPS'),"
        "'RAPS Sample','RAPS','');\n"
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=APPLICATION_PROTOCOL_DEFINITION('','automotive_design',2010,#2);\n"
        "#2=APPLICATION_CONTEXT('automotive design');\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n",
        encoding="utf-8",
    )


def _generate_rvt(path: Path) -> None:
    """Generate a binary file with Revit OLE Compound Document magic bytes.

    Real RVT files are OLE2 compound documents. The magic bytes are
    D0 CF 11 E0 A1 B1 1A E1 followed by a 512-byte header.
    """
    magic = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
    # OLE2 header: minor version, major version, byte order, sector size, etc.
    header = bytearray(512)
    header[0:8] = magic
    header[24:26] = b'\x3E\x00'  # Minor version
    header[26:28] = b'\x03\x00'  # Major version (3 = V3)
    header[28:30] = b'\xFE\xFF'  # Byte order (little-endian)
    header[30:32] = b'\x09\x00'  # Sector size power (2^9 = 512)
    header[32:34] = b'\x06\x00'  # Mini sector size power (2^6 = 64)
    # Pad to 1KB with deterministic pattern
    padding = bytes(range(256)) * 2  # 512 bytes of pattern
    path.write_bytes(bytes(header) + padding)


def _generate_dwg(path: Path) -> None:
    """Generate a binary file with DWG magic bytes (AutoCAD 2018+ format).

    DWG files start with a 6-byte version string (AC1032 for 2018+).
    """
    magic = b'AC1032'  # AutoCAD 2018 format
    # DWG header: magic + version data + padding
    header = bytearray(512)
    header[0:6] = magic
    header[6] = 0x00   # Maintenance version
    header[7] = 0x01   # One byte after version
    # The rest is zero-padded (minimal valid header)
    path.write_bytes(bytes(header))


def _generate_csvs(test_data: Path) -> None:
    """Generate CSV fixture files with realistic test data."""
    # Bulk users CSV (for admin bulk import tests)
    (test_data / "bulk-users.csv").write_text(
        "email,role\n"
        "user1@example.com,viewer\n"
        "user2@example.com,project_admin\n"
        "user3@example.com,viewer\n"
        "user4@example.com,project_admin\n"
        "user5@example.com,viewer\n",
        encoding="utf-8",
    )

    # Role updates CSV (for role change tests)
    (test_data / "role-updates.csv").write_text(
        "email,role\n"
        "user1@example.com,project_admin\n"
        "user2@example.com,viewer\n"
        "user3@example.com,project_admin\n",
        encoding="utf-8",
    )


def _generate_admin_csvs(test_data: Path) -> None:
    """Generate admin test data files at repo root (expected by admin tests)."""
    root = test_data.parent  # raps-examples root

    (root / "project-ids.txt").write_text(
        "b.demo-project-001\n"
        "b.demo-project-002\n"
        "b.demo-project-003\n",
        encoding="utf-8",
    )

    (root / "role-changes.csv").write_text(
        "email,role\n"
        "user@example.com,viewer\n"
        "admin@example.com,project_admin\n",
        encoding="utf-8",
    )

    (root / "new-users.csv").write_text(
        "email,role\n"
        "newuser@example.com,project_admin\n"
        "newuser2@example.com,viewer\n",
        encoding="utf-8",
    )
