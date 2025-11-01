"""Logging helpers for DI Simulation Engine."""


def configure_logger(fname: str) -> None:
    """Configure Loguru logging from a YAML file."""
    # TODO - use Path and var from constants here
    from pathlib import Path

    import yaml
    from loguru import logger

    fpath = Path(f"{fname}")
    with open(fpath, "r") as f:
        cfg = yaml.safe_load(f)
    logger.configure(**cfg)
    logger.info(f"Logger configured with settings from {fpath}")
