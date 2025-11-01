"""Simplified MongoDB seeder.

This script seeds a MongoDB database from JSON (or NDJSON) files located in
`database_seeds/`. The collection name is the seed filename (without extension),
e.g. `database_seeds/characters.json` -> collection `characters`.

No CLI, no switches — just run it. Minimal, readable, and type‑annotated.

Defaults
--------
- Database name: ``mydatabase`` (override with ``DB_NAME`` env var)
- Mongo URI: from ``MONGO_URI`` env var (``.env`` is auto‑loaded if available)
- Seeds dir: ``database_seeds/`` (all ``*.json`` and ``*.ndjson`` files)
- Behavior: drops each target collection, then inserts documents from the file

Example:
-------
$ poetry run python setup_new_database.py
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from bson import json_util
from pymongo.errors import CollectionInvalid

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    load_dotenv = None  # type: ignore

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

# --- Configuration -----------------------------------------------------------------
DEFAULT_DB_NAME: str = "dcs-db"
SEEDS_DIR: Path = Path("database_seeds")
SUPPORTED_EXTS = {".json", ".ndjson"}

INDEX_DEFS: dict[str, list[dict[str, Any]]] = {
    "characters": [{"fields": [("hid", 1)], "unique": True}],
    # Example:
    # "users": [
    #     {"fields": [("email", 1)], "unique": True},
    #     {"fields": [("last_login", -1)], "unique": False},
    # ],
}


# --- IO helpers --------------------------------------------------------------------


def backup_root_dir(db_name: str) -> Path:
    """Create and return a timestamped backup root directory."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    root = Path("database_backups") / f"{db_name}-{ts}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def backup_collection(db: Database, coll_name: str, root: Path) -> None:
    """Dump an existing collection to NDJSON + save index info."""
    coll = db[coll_name]
    out_path = root / f"{coll_name}.ndjson"
    idx_path = root / f"{coll_name}.__indexes__.json"

    # Stream to NDJSON in batches for large collections
    with out_path.open("w", encoding="utf-8") as f:
        cursor = coll.find({}, no_cursor_timeout=True).batch_size(1000)
        try:
            for doc in cursor:
                f.write(json_util.dumps(doc))
                f.write("\n")
        finally:
            cursor.close()

    # Save index info (structure, not data)
    with idx_path.open("w", encoding="utf-8") as f:
        json.dump(coll.index_information(), f, default=json_util.default, indent=2)


def load_seed_documents(path: Path) -> List[Dict[str, Any]]:
    """Load documents from a seed file.

    Accepts a JSON array (``[ {...}, {...} ]``), an object wrapper with a
    ``documents`` array, or newline‑delimited JSON (NDJSON).

    Parameters
    ----------
    path : Path
        Filesystem path to the seed file.

    Returns:
    -------
    List[Dict[str, Any]]
        Parsed documents; may be empty if the file is empty.

    Raises:
    ------
    ValueError
        If the file contents are not valid/usable JSON documents.
    """
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        logging.warning("%s is empty; skipping.", path)
        return []

    if path.suffix.lower() == ".ndjson":
        docs: List[Dict[str, Any]] = []
        for i, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"Line {i} in {path} is not a JSON object.")
            docs.append(obj)
        return docs

    data = json.loads(text)
    if isinstance(data, list):
        if not all(isinstance(x, dict) for x in data):
            raise ValueError(f"Array in {path} must contain only objects.")
        return data  # type: ignore[return-value]
    if (
        isinstance(data, dict)
        and "documents" in data
        and isinstance(data["documents"], list)
    ):
        docs = data["documents"]
        if not all(isinstance(x, dict) for x in docs):
            raise ValueError(f"'documents' in {path} must be an array of objects.")
        return docs  # type: ignore[return-value]

    raise ValueError(
        f"Unsupported JSON structure in {path}. Expected array, NDJSON, or \
            object with 'documents'."
    )


def discover_seed_files(seeds_dir: Path) -> List[Path]:
    """Return all supported seed files under ``seeds_dir`` (non‑recursive).

    Files are processed in alphabetical order for determinism.
    """
    return [
        p
        for p in sorted(seeds_dir.iterdir())
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    ]


# --- Mongo helpers -----------------------------------------------------------------


def get_client(uri: str) -> MongoClient:
    """Create a MongoDB client for the given URI."""
    return MongoClient(uri)


def seed_collection(coll: Collection, docs: Sequence[Dict[str, Any]]) -> int:
    """Replace a collection's contents with the given documents."""
    coll.drop()

    if not docs:
        logging.info("Dropped '%s'; creating empty collection.", coll.name)
        try:
            coll.database.create_collection(coll.name)
        except CollectionInvalid:
            pass
        return 0

    result = coll.insert_many(list(docs), ordered=False)
    return len(result.inserted_ids)


def create_indices(coll: Collection) -> None:
    """Create indices defined in INDEX_DEFS."""
    defs = INDEX_DEFS.get(coll.name)
    if not defs:
        return
    for spec in defs:
        fields = spec["fields"]
        unique = spec.get("unique", False)
        coll.create_index(fields, unique=unique)
        logging.info("Created index on %s: %s (unique=%s)", coll.name, fields, unique)


def seed_database(db: Database, seed_files: Iterable[Path]) -> None:
    """Seed all collections for the provided seed files."""
    existing = set(db.list_collection_names())
    backup_root: Path | None = None

    for f in seed_files:
        collection_name = f.stem

        # If the collection exists, back it up once per run
        if collection_name in existing:
            if backup_root is None:
                backup_root = backup_root_dir(db.name)
                logging.info("Backing up existing collections to %s", backup_root)
            try:
                logging.info("Backing up existing '%s'...", collection_name)
                backup_collection(db, collection_name, backup_root)
            except Exception as e:
                logging.error("Backup failed for '%s': %s", collection_name, e)
                raise  # Fail fast so we don't lose data

        logging.info("Seeding collection '%s' from %s", collection_name, f.name)
        docs = load_seed_documents(f)
        inserted = seed_collection(db[collection_name], docs)
        logging.info("Inserted %d document(s) into '%s'", inserted, collection_name)
        create_indices(db[collection_name])


# --- Entrypoint --------------------------------------------------------------------


def main() -> None:
    """Run the seeding process with built‑in defaults.

    Environment
    ----------
    MONGO_URI : str
        Full MongoDB connection string (required). If a ``.env`` file is
        present and ``python-dotenv`` is installed, it will be auto‑loaded.
    DB_NAME : str, optional
        Database name override (defaults to ``mydatabase``).
    """
    if load_dotenv is not None:
        try:
            load_dotenv()
        except Exception:  # pragma: no cover
            pass

    mongo_uri = os.getenv("MONGO_URI", "").strip()
    if not mongo_uri:
        raise SystemExit(
            "MONGO_URI is not set. Add it to your environment or .env file."
        )

    db_name = os.getenv("DB_NAME", DEFAULT_DB_NAME)

    if not SEEDS_DIR.exists() or not SEEDS_DIR.is_dir():
        raise SystemExit(f"Seeds directory not found: {SEEDS_DIR}")

    seed_paths = discover_seed_files(SEEDS_DIR)
    if not seed_paths:
        raise SystemExit(
            f"No seed files found in {SEEDS_DIR} (expected *.json or *.ndjson)."
        )

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logging.info("Connecting to MongoDB and seeding database '%s'...", db_name)

    client = get_client(mongo_uri)
    try:
        db = client[db_name]
        seed_database(db, seed_paths)
        logging.info("Done.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
