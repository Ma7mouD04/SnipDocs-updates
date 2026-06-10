"""Parse, compare, and manage SnipDocs version metadata."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional


class VersionError(Exception):
    """Raised when version data is invalid or cannot be loaded."""


class VersionManager:
    """Manages a SnipDocs ``version.json`` file.

    Parameters
    ----------
    path : str
        Filesystem path to the version JSON file.
    """

    REQUIRED_KEYS = {"version", "download_url", "message"}
    _VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$")

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
            raise VersionError("Version data not loaded. Call load() first.")
        return self._data

    # -- public API ----------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """Read and parse the version JSON file.

        Raises
        ------
        VersionError
            On missing file, malformed JSON, or non-object content.
        """
        if not os.path.isfile(self._path):
            raise VersionError(f"Version file not found: {self._path}")

        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise VersionError(f"Invalid JSON in {self._path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise VersionError(
                f"Expected a JSON object at top level, got {type(raw).__name__}"
            )

        self._data = raw
        return raw

    def validate(self) -> list[str]:
        """Validate loaded version data against expected schema.

        Returns
        -------
        list[str]
            Validation errors (empty when valid).
        """
        errors: list[str] = []
        data = self.data

        missing = self.REQUIRED_KEYS - set(data.keys())
        if missing:
            errors.append(f"Missing required keys: {sorted(missing)}")

        if "version" in data:
            if not isinstance(data["version"], str):
                errors.append(
                    f"'version' must be a string, got {type(data['version']).__name__}"
                )
            elif not self._VERSION_RE.match(data["version"]):
                errors.append(
                    f"'version' does not match expected format (e.g. '2.0' or '2.0.1'): "
                    f"'{data['version']}'"
                )

        if "download_url" in data and not isinstance(data["download_url"], str):
            errors.append(
                f"'download_url' must be a string, got {type(data['download_url']).__name__}"
            )

        if "message" in data and not isinstance(data["message"], str):
            errors.append(
                f"'message' must be a string, got {type(data['message']).__name__}"
            )

        return errors

    @staticmethod
    def parse_version(version_str: str) -> tuple[int, int, int]:
        """Parse a version string into a ``(major, minor, patch)`` tuple.

        Supports formats like ``"2"``, ``"2.0"``, ``"2.0.1"``.

        Raises
        ------
        VersionError
            If the string cannot be parsed.
        """
        match = VersionManager._VERSION_RE.match(version_str)
        if not match:
            raise VersionError(f"Invalid version string: '{version_str}'")
        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) is not None else 0
        patch = int(match.group(3)) if match.group(3) is not None else 0
        return (major, minor, patch)

    def get_version(self) -> str:
        """Return the version string from loaded data."""
        data = self.data
        if "version" not in data:
            raise VersionError("'version' key is missing")
        return str(data["version"])

    def get_version_tuple(self) -> tuple[int, int, int]:
        """Return the version as a ``(major, minor, patch)`` tuple."""
        return self.parse_version(self.get_version())

    def get_download_url(self) -> str:
        """Return the download URL."""
        data = self.data
        if "download_url" not in data:
            raise VersionError("'download_url' key is missing")
        return str(data["download_url"])

    def get_message(self) -> str:
        """Return the message string."""
        data = self.data
        if "message" not in data:
            raise VersionError("'message' key is missing")
        return str(data["message"])

    def is_newer_than(self, other_version: str) -> bool:
        """Check whether the loaded version is strictly newer than *other_version*."""
        return self.get_version_tuple() > self.parse_version(other_version)

    def set_version(self, version: str) -> None:
        """Set a new version string (validated)."""
        if not self._VERSION_RE.match(version):
            raise VersionError(f"Invalid version string: '{version}'")
        self.data["version"] = version

    def set_download_url(self, url: str) -> None:
        self.data["download_url"] = url

    def set_message(self, message: str) -> None:
        self.data["message"] = message

    def save(self, path: Optional[str] = None) -> None:
        """Persist version data to disk."""
        dest = path or self._path
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2)
            fh.write("\n")

    @staticmethod
    def compare_versions(v1: str, v2: str) -> int:
        """Compare two version strings.

        Returns
        -------
        int
            ``-1`` if *v1* < *v2*, ``0`` if equal, ``1`` if *v1* > *v2*.
        """
        t1 = VersionManager.parse_version(v1)
        t2 = VersionManager.parse_version(v2)
        if t1 < t2:
            return -1
        if t1 > t2:
            return 1
        return 0
