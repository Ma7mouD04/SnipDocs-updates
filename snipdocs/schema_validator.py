"""Generic JSON schema validation for SnipDocs data files."""

from __future__ import annotations

import json
import os
from typing import Any, Optional, Sequence


class SchemaValidationError(Exception):
    """Raised when JSON data fails schema validation."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation failed with {len(errors)} error(s): {errors}")


FieldSpec = dict[str, Any]
"""A mapping from field name to expected Python type (or a dict of constraints)."""


CONFIG_SCHEMA: dict[str, FieldSpec] = {
    "allowed": {"type": bool, "required": True},
    "message": {"type": str, "required": True},
}

VERSION_SCHEMA: dict[str, FieldSpec] = {
    "version": {"type": str, "required": True},
    "download_url": {"type": str, "required": True},
    "message": {"type": str, "required": True},
}


class SchemaValidator:
    """Validates JSON data against a simple field-spec schema.

    Parameters
    ----------
    schema : dict[str, FieldSpec]
        Mapping of field names to ``{"type": <type>, "required": bool}``.
    """

    def __init__(self, schema: dict[str, FieldSpec]) -> None:
        self._schema = schema

    @property
    def schema(self) -> dict[str, FieldSpec]:
        return dict(self._schema)

    def validate(self, data: dict[str, Any]) -> list[str]:
        """Validate *data* and return a list of error strings (empty → valid)."""
        errors: list[str] = []

        if not isinstance(data, dict):
            return [f"Expected a JSON object, got {type(data).__name__}"]

        for field, spec in self._schema.items():
            required = spec.get("required", False)
            expected_type = spec.get("type")

            if field not in data:
                if required:
                    errors.append(f"Missing required field: '{field}'")
                continue

            value = data[field]
            if expected_type is not None and not isinstance(value, expected_type):
                errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(value).__name__}"
                )

        return errors

    def validate_or_raise(self, data: dict[str, Any]) -> None:
        """Like :meth:`validate` but raises on failure."""
        errors = self.validate(data)
        if errors:
            raise SchemaValidationError(errors)

    def validate_file(self, path: str) -> list[str]:
        """Load a JSON file from *path* and validate its contents.

        Returns
        -------
        list[str]
            Validation errors. An empty list means the file is valid.
        """
        if not os.path.isfile(path):
            return [f"File not found: {path}"]

        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            return [f"Invalid JSON: {exc}"]

        return self.validate(data)

    def required_fields(self) -> list[str]:
        """Return a sorted list of required field names."""
        return sorted(
            name
            for name, spec in self._schema.items()
            if spec.get("required", False)
        )

    def optional_fields(self) -> list[str]:
        """Return a sorted list of optional field names."""
        return sorted(
            name
            for name, spec in self._schema.items()
            if not spec.get("required", False)
        )

    @staticmethod
    def validate_json_string(raw: str) -> tuple[Optional[Any], Optional[str]]:
        """Try to parse a raw JSON string.

        Returns
        -------
        tuple
            ``(parsed_data, None)`` on success, ``(None, error_message)`` on failure.
        """
        try:
            data = json.loads(raw)
            return data, None
        except json.JSONDecodeError as exc:
            return None, str(exc)
