"""Entrypoint script to run the FastAPI API server.

This script wraps uvicorn, sets up project logging via the existing
`configs/logger-api.config.yml` file, and exposes CLI flags so you
don't have to remember the full uvicorn command.

Example:
    python scripts/run_api.py --host 0.0.0.0 --port 8000 --reload

Notes:
    - Uses the same `configure_logger` helper as run_cli.py
    - The uvicorn reloader requires the import string
      "dcs_simulation_engine.api.main:app"
    - Configure rotation, retention, and formatting in
      configs/logger-api.config.yml
"""

import argparse
import os
from pathlib import Path

import uvicorn
from loguru import logger

from dcs_simulation_engine.helpers.logging_helpers import configure_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the API runner.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Run the DCS Simulation Engine API")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (omit with --reload)",
    )
    parser.add_argument(
        "--log-config",
        default="configs/logger-api.config.yml",
        help="Path to Loguru logger configuration file",
    )
    return parser.parse_args()


def main() -> None:
    """Main entrypoint to start the FastAPI server with project logging."""
    args = parse_args()

    # Configure Loguru logging via YAML
    try:
        configure_logger(args.log_config)
    except Exception as e:
        logger.error(f"Failed to configure logger: {e}")
        return

    if args.reload and args.workers != 1:
        logger.warning("--reload implies a single worker; forcing workers=1")
        args.workers = 1

    # Ensure project root on PYTHONPATH so uvicorn can import correctly
    os.environ.setdefault("PYTHONPATH", str(Path(".").resolve()))

    logger.info(
        f"Starting API at http://{args.host}:{args.port} "
        f"(reload={args.reload}, workers={args.workers})"
    )

    uvicorn.run(
        "dcs_simulation_engine.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
