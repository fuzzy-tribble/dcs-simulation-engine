"""Tests for validation helpers."""

import textwrap
from pathlib import Path

import pytest

from dcs_simulation_engine.helpers.validation_helpers import validate_files_with_schema


@pytest.fixture
def sample_yaml_files(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    """Fixture to create sample YAML files and a schema."""
    schema_path = tmp_path / "test.schema.yml"
    schema_path.write_text(
        textwrap.dedent(
            """
    name: str(required=True)
    age: int(required=True)
    """
        )
    )

    # Valid YAML
    valid_yaml = tmp_path / "valid.yml"
    valid_yaml.write_text(
        textwrap.dedent(
            """
    name: Alice
    age: 30
    """
        )
    )

    # Invalid YAML (missing age)
    invalid_yaml = tmp_path / "invalid.yml"
    invalid_yaml.write_text(
        textwrap.dedent(
            """
    name: Bob
    """
        )
    )

    return tmp_path, schema_path, valid_yaml, invalid_yaml


def test_validate_files_with_schema(
    sample_yaml_files: tuple[Path, Path, Path, Path],
) -> None:
    """Should validate YAML files against a schema file."""
    tmp_path, schema_path, valid_yaml, invalid_yaml = sample_yaml_files

    # Run validation against all files in the directory
    results = validate_files_with_schema(target=tmp_path, schema_path=schema_path)

    # Both files are keys in the results
    assert valid_yaml in results
    assert invalid_yaml in results

    # Valid YAML should have no errors
    assert results[valid_yaml] == []

    # Invalid YAML should have at least one error
    assert len(results[invalid_yaml]) > 0
    print("Errors for invalid.yml:", results[invalid_yaml])
