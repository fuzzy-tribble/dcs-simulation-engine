"""API package for DCS Simulation Engine.

This package exposes a FastAPI application that wraps the core
`SimulationManager` to provide HTTP endpoints for loading, compiling,
stepping through, and playing simulations.

The package layout follows a standard FastAPI structure with routers,
dependency helpers, service layer (a simple in-memory registry), and
Pydantic models.

Notes:
    - Keep this package lightweight; heavy lifting belongs in `core/`.
    - Add auth/middleware in `main.py` if needed later.
"""
