#!/usr/bin/env python3
"""Convenience script.

Usage:

python create_player.py name="Cara" stats='{"str":10,"dex":14,"int":17}' tags='["new","beta"]'

python create_player.py name="Bob" level=3 --no-key
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from dcs_simulation_engine.helpers import database_helpers as dbh


def _parse_kv(pairs: list[str]) -> Dict[str, Any]:
    """Parse key=value tokens into a dict.

    Values accept JSON (e.g., true, 123, {"a":1}).
    """
    out: Dict[str, Any] = {}
    for token in pairs:
        if "=" not in token:
            raise SystemExit(f"bad field (expected key=value): {token!r}")
        k, v = token.split("=", 1)
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def main(argv: list[str] | None = None) -> int:
    """Convenience script wrapper around dbh.create_player."""
    ap = argparse.ArgumentParser(
        description="Create a player and print id + access key."
    )
    ap.add_argument(
        "fields", nargs="*", help="player fields as key=value (values may be JSON)"
    )
    ap.add_argument(
        "--id", dest="player_id", help="explicit player _id to upsert", default=None
    )
    ap.add_argument(
        "--no-key", action="store_true", help="do not issue a new access key"
    )
    ns = ap.parse_args(argv)

    data = _parse_kv(ns.fields)
    player_id, raw_key = dbh.create_player(
        data,
        player_id=ns.player_id,
        issue_access_key=not ns.no_key,
        return_raw_key=True,  # ensure raw_key is returned if issued
    )

    print(f"id={player_id}")
    print(f"access_key={raw_key if raw_key else 'None'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
