"""File utility functions."""

from pathlib import Path


def safe_timestamp() -> str:
    """Returns a timestamp string safe for file names."""
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d_%H%M%S")


def unique_fpath(path: Path) -> Path:
    """Returns an incremented unique file path to avoid overwriting existing files."""
    path = Path(path)
    if not path.exists():
        return path

    parent, stem, suffix = path.parent, path.stem, path.suffix
    counter = 1
    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1
