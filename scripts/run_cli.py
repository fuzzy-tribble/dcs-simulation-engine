"""Module to run using cli interface."""

import argparse

from loguru import logger

from dcs_simulation_engine.cli.runner import run_cli
from dcs_simulation_engine.helpers.logging_helpers import configure_logger


def main() -> None:
    """Main entrypoint for running the CLI."""
    logger.info("Starting CLI.")

    parser = argparse.ArgumentParser(description="CLI runner entrypoint")
    parser.add_argument(
        "-g",
        "--game",
        type=str,
        required=True,
        help="Name of the game to launch (default: explore).",
    )
    parser.add_argument("--access-key", type=str, default=None)
    parser.add_argument("--pc-choice", type=str, default=None)
    parser.add_argument("--npc-choice", type=str, default=None)
    parser.add_argument("--source", type=str, default=None)

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Show info logs (-v) or debug (-vv) to console",
    )

    args = parser.parse_args()

    if args.source is None:
        logger.warning(
            "No source was provided for run, defaulting to 'cli-default'."
            " Source helps track the origin of the simulation in database entries, etc."
        )
        args.source = "cli-default"

    try:
        configure_logger(source=args.source)
    except Exception as e:
        logger.warning(f"Failed to configure logger with source '{args.source}': {e}")

    # --- configure console side channel based on -v
    if args.verbose > 0:
        level = "DEBUG" if args.verbose > 1 else "INFO"
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>",
        )

    try:
        run_cli(
            game=args.game,
            source=args.source,
            pc_choice=args.pc_choice,
            npc_choice=args.npc_choice,
            access_key=args.access_key,
        )
    except Exception as e:
        logger.exception(f"Exception occurred while running the CLI: {e}")
        print("Error occurred while running the CLI. Stopping. Check logs for details.")
    finally:
        logger.info("CLI exited.")


if __name__ == "__main__":
    import sys

    main()
