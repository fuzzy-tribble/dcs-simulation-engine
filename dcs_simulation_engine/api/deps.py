"""Dependency utilities for route handlers.

Provides reusable dependency functions for resolving shared services
and objects (e.g., looking up a SimulationManager by ID).
"""

from fastapi import Depends, HTTPException

from dcs_simulation_engine.api.services.registry import SimRegistry, get_registry


def get_manager(sim_id: str, registry: SimRegistry = Depends(get_registry)):
    """Resolve a SimulationManager from the registry.

    Args:
        sim_id (str): Identifier of a simulation in the registry.
        registry (SimRegistry): The in-memory registry (injected).

    Returns:
        SimulationManager: The simulation manager instance.

    Raises:
        HTTPException: If the simulation ID is not found in the registry.
    """
    mgr = registry.get(sim_id)
    if mgr is None:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return mgr
