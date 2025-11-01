"""Temp smoketest for API."""

import pytest


@pytest.mark.skip(reason="Smoketest only")
def test_can_import_api() -> None:
    """Ensure the main API module and FastAPI app can be imported."""
    import dcs_simulation_engine.api.main as m

    assert m.app
