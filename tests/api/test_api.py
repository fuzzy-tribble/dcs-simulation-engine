"""Tests for the API module."""

import pytest


@pytest.mark.unit
def test_can_import_api() -> None:
    """Ensure the main API module and FastAPI app can be imported."""
    import dcs_simulation_engine.api.main as m

    assert m.app


@pytest.mark.skip(reason="API server startup test not implemented yet")
def test_can_start_api_server() -> None:
    """Ensure the API server can be started."""
    pass
