"""Main entrypoint for the DCS Simulation Engine API.

Sets up the FastAPI application, middleware, and routes. Serves the
auto-generated OpenAPI/Swagger UI at `/docs` and Redoc at `/redoc`.

Example:
    Run the API server using uvicorn:

        uvicorn api.main:app --reload

Notes/Assumptions:
    - CORS is wide-open by default for dev convenience; lock it down in prod.
    - The `app` object is created at import time so uvicorn can discover it.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dcs_simulation_engine.api.routers import simulations
from dcs_simulation_engine.api.settings import settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI app.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title="DCS Simulation Engine API",
        version="0.1.0",
        description="FastAPI wrapper for dcs-simulation-engine",
        contact={"name": "DCS Simulation Team"},
    )

    # Notes:
    # - In development, allow all origins for ease of local integration/testing.
    # - In production, set DCS_API_CORS_ALLOW_ALL=false and add allowlist logic.
    if settings.cors_allow_all:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Route registration
    app.include_router(simulations.router, prefix="/v1", tags=["simulations"])
    return app


app = create_app()
