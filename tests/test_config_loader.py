"""Tests for snipdocs.config_loader."""

import json
import os
import tempfile

import pytest

from snipdocs.config_loader import ConfigError, ConfigLoader


@pytest.fixture()
def valid_config(tmp_path):
    """Write a valid config.json and return its path."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"allowed": True, "message": ""}), encoding="utf-8")
    return str(path)


@pytest.fixture()
def loader(valid_config):
    return ConfigLoader(valid_config)


# -- construction & properties -----------------------------------------------

class TestConstruction:
    def test_path_stored(self, valid_config):
        loader = ConfigLoader(valid_config)
        assert loader.path == valid_config

    def test_data_before_load_raises(self, valid_config):
        loader = ConfigLoader(valid_config)
        with pytest.raises(ConfigError, match="not loaded"):
            _ = loader.data


# -- load() ------------------------------------------------------------------

class TestLoad:
    def test_load_valid(self, loader):
        data = loader.load()
        assert data == {"allowed": True, "message": ""}

    def test_load_sets_data(self, loader):
        loader.load()
        assert loader.data["allowed"] is True

    def test_load_missing_file(self, tmp_path):
        loader = ConfigLoader(str(tmp_path / "nope.json"))
        with pytest.raises(ConfigError, match="not found"):
            loader.load()

    def test_load_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad", encoding="utf-8")
        loader = ConfigLoader(str(path))
        with pytest.raises(ConfigError, match="Invalid JSON"):
            loader.load()

    def test_load_non_object(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text("[1, 2]", encoding="utf-8")
        loader = ConfigLoader(str(path))
        with pytest.raises(ConfigError, match="Expected a JSON object"):
            loader.load()


# -- validate() --------------------------------------------------------------

class TestValidate:
    def test_valid_config(self, loader):
        loader.load()
        assert loader.validate() == []

    def test_missing_allowed(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"message": ""}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        errors = loader.validate()
        assert any("allowed" in e for e in errors)

    def test_missing_message(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": True}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        errors = loader.validate()
        assert any("message" in e for e in errors)

    def test_wrong_type_allowed(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": "yes", "message": ""}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        errors = loader.validate()
        assert any("boolean" in e for e in errors)

    def test_wrong_type_message(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": True, "message": 123}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        errors = loader.validate()
        assert any("string" in e for e in errors)

    def test_extra_keys_accepted(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(
            json.dumps({"allowed": True, "message": "", "extra": 1}),
            encoding="utf-8",
        )
        loader = ConfigLoader(str(path))
        loader.load()
        assert loader.validate() == []


# -- is_allowed() / get_message() -------------------------------------------

class TestAccessors:
    def test_is_allowed_true(self, loader):
        loader.load()
        assert loader.is_allowed() is True

    def test_is_allowed_false(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": False, "message": "no"}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        assert loader.is_allowed() is False

    def test_is_allowed_missing_key(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"message": ""}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        with pytest.raises(ConfigError, match="missing"):
            loader.is_allowed()

    def test_get_message(self, loader):
        loader.load()
        assert loader.get_message() == ""

    def test_get_message_nonempty(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(
            json.dumps({"allowed": True, "message": "hello"}), encoding="utf-8"
        )
        loader = ConfigLoader(str(path))
        loader.load()
        assert loader.get_message() == "hello"

    def test_get_message_missing_key(self, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": True}), encoding="utf-8")
        loader = ConfigLoader(str(path))
        loader.load()
        with pytest.raises(ConfigError, match="missing"):
            loader.get_message()


# -- mutators & save() ------------------------------------------------------

class TestMutatorsAndSave:
    def test_set_allowed(self, loader):
        loader.load()
        loader.set_allowed(False)
        assert loader.data["allowed"] is False

    def test_set_message(self, loader):
        loader.load()
        loader.set_message("maintenance")
        assert loader.data["message"] == "maintenance"

    def test_save_default_path(self, loader, valid_config):
        loader.load()
        loader.set_message("saved")
        loader.save()
        with open(valid_config, "r", encoding="utf-8") as fh:
            reloaded = json.load(fh)
        assert reloaded["message"] == "saved"

    def test_save_custom_path(self, loader, tmp_path):
        loader.load()
        dest = str(tmp_path / "out.json")
        loader.save(dest)
        with open(dest, "r", encoding="utf-8") as fh:
            reloaded = json.load(fh)
        assert reloaded == loader.data
