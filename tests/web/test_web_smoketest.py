"""Tests for web smoketest and loadtest."""

# TODO: pre v001 add web smoketest

# TODO: pre-live-release - consider adding loadtest for concurrent runs

import pytest


@pytest.mark.skip(reason="Smoketest only")
def test_can_import() -> None:
    """Ensure the main web module and FastAPI app can be imported."""
    pass
