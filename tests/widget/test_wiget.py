"""Tests for widget module."""

import pytest


@pytest.mark.unit
def test_can_import() -> None:
    """Ensure the main widget module can be imported."""
    import dcs_simulation_engine.widget.app as app

    assert app.build_app


@pytest.mark.skip(reason="Widget startup test not implemented yet")
def test_can_start_widget() -> None:
    """Ensure the widget can be started."""
    pass
