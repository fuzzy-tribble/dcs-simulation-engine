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
