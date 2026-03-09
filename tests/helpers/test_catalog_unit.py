"""Unit tests for catalog variable resolution."""
from __future__ import annotations

import pytest

from tests.test_catalog import _resolve


def test_resolve_substitutes_known_var():
    assert _resolve("raps hub list ${hub_id}", {"hub_id": "b.123"}) == "raps hub list b.123"


def test_resolve_multiple_vars():
    cmd = _resolve(
        "raps project list ${hub_id} --project ${project_id}",
        {"hub_id": "b.1", "project_id": "p.2"},
    )
    assert cmd == "raps project list b.1 --project p.2"


def test_resolve_unresolved_var_raises():
    """Unresolved ${var} must cause pytest.fail(), not silent passthrough."""
    with pytest.raises(pytest.fail.Exception):
        _resolve("raps folder create ${missing_var}", {})


def test_resolve_env_var_takes_priority(monkeypatch):
    """RAPS_VAR_HUB_ID env var must override the variables dict."""
    monkeypatch.setenv("RAPS_VAR_HUB_ID", "env-hub")
    result = _resolve("raps hub list ${hub_id}", {"hub_id": "dict-hub"})
    assert result == "raps hub list env-hub"
