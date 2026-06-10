"""Tests for snipdocs.schema_validator."""

import json

import pytest

from snipdocs.schema_validator import (
    CONFIG_SCHEMA,
    VERSION_SCHEMA,
    SchemaValidationError,
    SchemaValidator,
)


@pytest.fixture()
def config_validator():
    return SchemaValidator(CONFIG_SCHEMA)


@pytest.fixture()
def version_validator():
    return SchemaValidator(VERSION_SCHEMA)


# -- schema property ---------------------------------------------------------

class TestSchemaProperty:
    def test_returns_copy(self, config_validator):
        schema = config_validator.schema
        schema["extra"] = {}
        assert "extra" not in config_validator.schema


# -- validate() with CONFIG_SCHEMA ------------------------------------------

class TestConfigValidation:
    def test_valid(self, config_validator):
        assert config_validator.validate({"allowed": True, "message": ""}) == []

    def test_missing_allowed(self, config_validator):
        errors = config_validator.validate({"message": ""})
        assert any("allowed" in e for e in errors)

    def test_missing_message(self, config_validator):
        errors = config_validator.validate({"allowed": True})
        assert any("message" in e for e in errors)

    def test_wrong_type_allowed(self, config_validator):
        errors = config_validator.validate({"allowed": "yes", "message": ""})
        assert any("bool" in e for e in errors)

    def test_wrong_type_message(self, config_validator):
        errors = config_validator.validate({"allowed": True, "message": 0})
        assert any("str" in e for e in errors)

    def test_non_dict(self, config_validator):
        errors = config_validator.validate([1, 2])
        assert any("object" in e for e in errors)

    def test_extra_fields_ok(self, config_validator):
        assert config_validator.validate({"allowed": True, "message": "", "x": 1}) == []


# -- validate() with VERSION_SCHEMA -----------------------------------------

class TestVersionValidation:
    def test_valid(self, version_validator):
        data = {"version": "2.0", "download_url": "", "message": ""}
        assert version_validator.validate(data) == []

    def test_missing_all(self, version_validator):
        errors = version_validator.validate({})
        assert len(errors) == 3

    def test_wrong_types(self, version_validator):
        data = {"version": 2, "download_url": 0, "message": False}
        errors = version_validator.validate(data)
        assert len(errors) == 3


# -- validate_or_raise() ----------------------------------------------------

class TestValidateOrRaise:
    def test_valid_no_raise(self, config_validator):
        config_validator.validate_or_raise({"allowed": True, "message": ""})

    def test_invalid_raises(self, config_validator):
        with pytest.raises(SchemaValidationError) as exc_info:
            config_validator.validate_or_raise({})
        assert len(exc_info.value.errors) == 2


# -- validate_file() --------------------------------------------------------

class TestValidateFile:
    def test_valid_file(self, config_validator, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(
            json.dumps({"allowed": True, "message": ""}), encoding="utf-8"
        )
        assert config_validator.validate_file(str(path)) == []

    def test_missing_file(self, config_validator, tmp_path):
        errors = config_validator.validate_file(str(tmp_path / "nope.json"))
        assert any("not found" in e for e in errors)

    def test_invalid_json(self, config_validator, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad", encoding="utf-8")
        errors = config_validator.validate_file(str(path))
        assert any("Invalid JSON" in e for e in errors)

    def test_file_with_wrong_schema(self, config_validator, tmp_path):
        path = tmp_path / "c.json"
        path.write_text(json.dumps({"allowed": "nope", "message": 0}), encoding="utf-8")
        errors = config_validator.validate_file(str(path))
        assert len(errors) == 2


# -- required_fields / optional_fields ---------------------------------------

class TestFieldLists:
    def test_required_config(self, config_validator):
        assert config_validator.required_fields() == ["allowed", "message"]

    def test_required_version(self, version_validator):
        assert version_validator.required_fields() == [
            "download_url",
            "message",
            "version",
        ]

    def test_optional_empty(self, config_validator):
        assert config_validator.optional_fields() == []

    def test_optional_with_optional(self):
        schema = {
            "a": {"type": str, "required": True},
            "b": {"type": int, "required": False},
        }
        v = SchemaValidator(schema)
        assert v.optional_fields() == ["b"]


# -- validate_json_string() -------------------------------------------------

class TestValidateJsonString:
    def test_valid(self):
        data, err = SchemaValidator.validate_json_string('{"a": 1}')
        assert err is None
        assert data == {"a": 1}

    def test_invalid(self):
        data, err = SchemaValidator.validate_json_string("{bad")
        assert data is None
        assert err is not None

    def test_array(self):
        data, err = SchemaValidator.validate_json_string("[1, 2]")
        assert data == [1, 2]
        assert err is None
