"""Miscellaneous utility functions for DCS Simulation Engine."""

import json
import pickle
from typing import Any


def byte_size_json(obj: Any) -> int:
    """Return the size in bytes of the JSON-encoded object."""
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def byte_size_pickle(obj: Any) -> int:
    """Return the size in bytes of the pickled object."""
    return len(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL))


def make_human_readable_values(data: dict[str, Any]) -> dict[str, str]:
    """Recursively clean and humanize all values in a dict.

    Without changing the overall structure (lists stay lists,
    dicts stay dicts).
    """
    if isinstance(data, dict):
        return {k: make_human_readable_values(v) for k, v in data.items()}

    if isinstance(data, list):
        return [make_human_readable_values(v) for v in data]

    # primitives → return cleaned version
    if isinstance(data, str):
        return data.strip()

    return data
