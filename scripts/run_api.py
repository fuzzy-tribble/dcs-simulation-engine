"""Entrypoint to run the FastAPI API server.

Example:
    poetry run python -m scripts.run_api
    poetry run python scripts/run_api.py --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

import uvicorn
from loguru import logger

from dcs_simulation_engine.helpers.logging_helpers import configure_logger


def _port(value: str) -> int:
    """Validate and return a TCP port.

    Args:
        value: Port value provided as a string.

    Returns:
        A valid TCP port number.

    Raises:
        argparse.ArgumentTypeError: If the value is not an integer in [1, 65535].
    """
    try:
        port = int(value)
    except ValueError as e:
        raise argparse.ArgumentTypeError("port must be an integer") from e
    if not (1 <= port <= 65535):
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the API runner.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description="FastAPI API runner entrypoint")

    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host interface to bind the API server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=_port,
        default=8000,
        help="Port to run the API server on (default: 8000).",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (ignored when --reload is set).",
    )
    parser.add_argument(
        "--log-config",
        type=str,
        default="configs/logger-api.config.yml",
        help="Path to a logging config YAML for the API runner.",
    )
    parser.add_argument(
        "--banner",
        type=str,
        default=None,
        help="Optional HTML/markdown banner to pass into the app for docs.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase console verbosity: -v for INFO, -vv for DEBUG.",
    )
    # TODO: add source argument to help track origin of API runs
    return parser.parse_args()


def _effective_workers(reload: bool, requested_workers: int) -> Optional[int]:
    """Compute the effective worker count for uvicorn.

    Args:
        reload: Whether hot-reload is enabled.
        requested_workers: The requested worker count.

    Returns:
        None if uvicorn should decide (or enforce single when reloading),
        otherwise a positive integer.

    Notes:
        uvicorn ignores `workers` when `reload=True`; passing None is cleanest.
    """
    if reload:
        if requested_workers != 1:
            logger.warning("--reload implies a single process; ignoring --workers")
        return None
    if requested_workers < 1:
        logger.warning("workers must be >= 1; forcing workers=1")
        return 1
    return requested_workers


def run(args: argparse.Namespace) -> int:
    """Run the FastAPI app with the provided arguments.

    Builds a uvicorn.Server and executes it, handling common exceptions.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code: 0 on clean shutdown, 130 on SIGINT, 1 on error.
    """
    try:
        workers = _effective_workers(args.reload, args.workers)

        # Log a concise startup line
        logger.info(
            f"Starting API ({args.host}:{args.port}) "
            f"(reload={args.reload}, workers={workers if workers else 1})"
        )

        # If you need to inject `banner` into the app, expose a factory like:
        #   app = create_app(banner=args.banner)
        # and use `Config(app=app)` with `factory=True`.
        config = uvicorn.Config(
            "dcs_simulation_engine.api.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=workers,
            # Hand logging to Loguru; avoid uvicorn's default dictConfig
            log_config=None,
        )
        server = uvicorn.Server(config)

        # server.run() returns True on successful shutdown, False on failure
        return 0 if server.run() else 1

    except KeyboardInterrupt:
        logger.info("Received interrupt. Shutting down...")
        return 130
    except Exception:
        logger.exception("API server crashed")
        return 1


def main() -> None:
    """Main entrypoint for running the API server.

    Parses args, configures logging, optionally adjusts console verbosity,
    and exits with the code returned from `run(args)`.
    """
    args = parse_args()

    # Configure project logging
    try:
        configure_logger(args.log_config)
    except Exception as e:
        # Fall back to default Loguru sink but proceed
        logger.warning(
            f"Failed to load log config at '{args.log_config}'; "
            f"using default logger. ({e})"
        )

    # Optional console verbosity side channel
    if args.verbose > 0:
        level = "DEBUG" if args.verbose > 1 else "INFO"
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
        )

    code = run(args)
    sys.exit(code)


if __name__ == "__main__":
    main()
