"""Load, validate, and manage SnipDocs configuration files."""

from __future__ import annotations

import json
import os
from typing import Any, Optional


class ConfigError(Exception):
    """Raised when a configuration file is invalid or cannot be loaded."""


class ConfigLoader:
    """Loads and manages a SnipDocs ``config.json`` file.

    Parameters
    ----------
    path : str
        Filesystem path to the JSON configuration file.
    """

    REQUIRED_KEYS = {"allowed", "message"}

    def __init__(self, path: str) -> None:
        self._path = path
        self._data: Optional[dict[str, Any]] = None

    # -- properties ----------------------------------------------------------

    @property
    def path(self) -> str:
        return self._path

    @property
    def data(self) -> dict[str, Any]:
        if self._data is None:
            raise ConfigError("Configuration not loaded. Call load() first.")
        return self._data

    # -- public API ----------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """Read and parse the JSON config file.

        Returns
        -------
        dict
            The parsed configuration dictionary.

        Raises
        ------
        ConfigError
            If the file does not exist, is not valid JSON, or is not an object.
        """
        if not os.path.isfile(self._path):
            raise ConfigError(f"Config file not found: {self._path}")

        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in {self._path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ConfigError(
                f"Expected a JSON object at top level, got {type(raw).__name__}"
            )

        self._data = raw
        return raw

    def validate(self) -> list[str]:
        """Validate the loaded config against the expected schema.

        Returns
        -------
        list[str]
            A list of human-readable validation error strings (empty when valid).

        Raises
        ------
        ConfigError
            If ``load()`` has not been called yet.
        """
        errors: list[str] = []
        data = self.data

        missing = self.REQUIRED_KEYS - set(data.keys())
        if missing:
            errors.append(f"Missing required keys: {sorted(missing)}")

        if "allowed" in data and not isinstance(data["allowed"], bool):
            errors.append(
                f"'allowed' must be a boolean, got {type(data['allowed']).__name__}"
            )

        if "message" in data and not isinstance(data["message"], str):
            errors.append(
                f"'message' must be a string, got {type(data['message']).__name__}"
            )

        return errors

    def is_allowed(self) -> bool:
        """Return the value of the ``allowed`` flag.

        Raises
        ------
        ConfigError
            If the config has not been loaded or ``allowed`` is missing.
        """
        data = self.data
        if "allowed" not in data:
            raise ConfigError("'allowed' key is missing from config")
        return bool(data["allowed"])

    def get_message(self) -> str:
        """Return the ``message`` string from the config.

        Raises
        ------
        ConfigError
            If the config has not been loaded or ``message`` is missing.
        """
        data = self.data
        if "message" not in data:
            raise ConfigError("'message' key is missing from config")
        return str(data["message"])

    def save(self, path: Optional[str] = None) -> None:
        """Write the current config back to disk.

        Parameters
        ----------
        path : str, optional
            Destination path.  Defaults to the original ``self.path``.
        """
        dest = path or self._path
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)
            fh.write("\n")

    def set_allowed(self, value: bool) -> None:
        """Update the ``allowed`` flag in-memory."""
        data = self.data
        data["allowed"] = value

    def set_message(self, value: str) -> None:
        """Update the ``message`` value in-memory."""
        data = self.data
        data["message"] = value
