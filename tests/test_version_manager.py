"""Tests for snipdocs.version_manager."""

import json

import pytest

from snipdocs.version_manager import VersionError, VersionManager


@pytest.fixture()
def valid_version(tmp_path):
    path = tmp_path / "version.json"
    path.write_text(
        json.dumps({"version": "2.0", "download_url": "https://example.com", "message": ""}),
        encoding="utf-8",
    )
    return str(path)


@pytest.fixture()
def mgr(valid_version):
    return VersionManager(valid_version)


# -- construction ------------------------------------------------------------

class TestConstruction:
    def test_path(self, valid_version):
        mgr = VersionManager(valid_version)
        assert mgr.path == valid_version

    def test_data_before_load(self, valid_version):
        mgr = VersionManager(valid_version)
        with pytest.raises(VersionError, match="not loaded"):
            _ = mgr.data


# -- load() ------------------------------------------------------------------

class TestLoad:
    def test_load_valid(self, mgr):
        data = mgr.load()
        assert data["version"] == "2.0"

    def test_load_missing_file(self, tmp_path):
        mgr = VersionManager(str(tmp_path / "nope.json"))
        with pytest.raises(VersionError, match="not found"):
            mgr.load()

    def test_load_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json", encoding="utf-8")
        mgr = VersionManager(str(path))
        with pytest.raises(VersionError, match="Invalid JSON"):
            mgr.load()

    def test_load_non_object(self, tmp_path):
        path = tmp_path / "arr.json"
        path.write_text("[]", encoding="utf-8")
        mgr = VersionManager(str(path))
        with pytest.raises(VersionError, match="Expected a JSON object"):
            mgr.load()


# -- validate() --------------------------------------------------------------

class TestValidate:
    def test_valid(self, mgr):
        mgr.load()
        assert mgr.validate() == []

    def test_missing_version(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"download_url": "", "message": ""}), encoding="utf-8"
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("version" in e for e in errors)

    def test_missing_download_url(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"version": "1.0", "message": ""}), encoding="utf-8"
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("download_url" in e for e in errors)

    def test_invalid_version_format(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"version": "abc", "download_url": "", "message": ""}),
            encoding="utf-8",
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("format" in e for e in errors)

    def test_version_not_string(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"version": 2, "download_url": "", "message": ""}),
            encoding="utf-8",
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("string" in e for e in errors)

    def test_download_url_not_string(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"version": "1.0", "download_url": 123, "message": ""}),
            encoding="utf-8",
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("download_url" in e for e in errors)

    def test_message_not_string(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(
            json.dumps({"version": "1.0", "download_url": "", "message": False}),
            encoding="utf-8",
        )
        mgr = VersionManager(str(path))
        mgr.load()
        errors = mgr.validate()
        assert any("message" in e for e in errors)


# -- parse_version() --------------------------------------------------------

class TestParseVersion:
    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("1", (1, 0, 0)),
            ("2.0", (2, 0, 0)),
            ("1.2.3", (1, 2, 3)),
            ("0.0.0", (0, 0, 0)),
            ("10.20.30", (10, 20, 30)),
        ],
    )
    def test_valid(self, input_str, expected):
        assert VersionManager.parse_version(input_str) == expected

    @pytest.mark.parametrize("bad", ["", "abc", "1.2.3.4", "1.2.x", "-1.0"])
    def test_invalid(self, bad):
        with pytest.raises(VersionError, match="Invalid version"):
            VersionManager.parse_version(bad)


# -- get_* accessors ---------------------------------------------------------

class TestAccessors:
    def test_get_version(self, mgr):
        mgr.load()
        assert mgr.get_version() == "2.0"

    def test_get_version_tuple(self, mgr):
        mgr.load()
        assert mgr.get_version_tuple() == (2, 0, 0)

    def test_get_download_url(self, mgr):
        mgr.load()
        assert mgr.get_download_url() == "https://example.com"

    def test_get_message(self, mgr):
        mgr.load()
        assert mgr.get_message() == ""

    def test_get_version_missing(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(json.dumps({"download_url": "", "message": ""}), encoding="utf-8")
        mgr = VersionManager(str(path))
        mgr.load()
        with pytest.raises(VersionError, match="missing"):
            mgr.get_version()

    def test_get_download_url_missing(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(json.dumps({"version": "1.0", "message": ""}), encoding="utf-8")
        mgr = VersionManager(str(path))
        mgr.load()
        with pytest.raises(VersionError, match="missing"):
            mgr.get_download_url()

    def test_get_message_missing(self, tmp_path):
        path = tmp_path / "v.json"
        path.write_text(json.dumps({"version": "1.0", "download_url": ""}), encoding="utf-8")
        mgr = VersionManager(str(path))
        mgr.load()
        with pytest.raises(VersionError, match="missing"):
            mgr.get_message()


# -- is_newer_than() --------------------------------------------------------

class TestIsNewerThan:
    def test_newer(self, mgr):
        mgr.load()
        assert mgr.is_newer_than("1.0") is True

    def test_equal(self, mgr):
        mgr.load()
        assert mgr.is_newer_than("2.0") is False

    def test_older(self, mgr):
        mgr.load()
        assert mgr.is_newer_than("3.0") is False


# -- compare_versions() -----------------------------------------------------

class TestCompareVersions:
    @pytest.mark.parametrize(
        "v1, v2, expected",
        [
            ("1.0", "2.0", -1),
            ("2.0", "2.0", 0),
            ("3.0", "2.0", 1),
            ("1.0.1", "1.0.0", 1),
            ("1.0.0", "1.0.1", -1),
            ("1", "1.0.0", 0),
        ],
    )
    def test_compare(self, v1, v2, expected):
        assert VersionManager.compare_versions(v1, v2) == expected


# -- mutators & save --------------------------------------------------------

class TestMutatorsAndSave:
    def test_set_version_valid(self, mgr):
        mgr.load()
        mgr.set_version("3.1.0")
        assert mgr.data["version"] == "3.1.0"

    def test_set_version_invalid(self, mgr):
        mgr.load()
        with pytest.raises(VersionError, match="Invalid"):
            mgr.set_version("bad")

    def test_set_download_url(self, mgr):
        mgr.load()
        mgr.set_download_url("https://new.example.com")
        assert mgr.data["download_url"] == "https://new.example.com"

    def test_set_message(self, mgr):
        mgr.load()
        mgr.set_message("updated")
        assert mgr.data["message"] == "updated"

    def test_save(self, mgr, valid_version):
        mgr.load()
        mgr.set_version("9.9.9")
        mgr.save()
        with open(valid_version, "r", encoding="utf-8") as fh:
            reloaded = json.load(fh)
        assert reloaded["version"] == "9.9.9"

    def test_save_custom_path(self, mgr, tmp_path):
        mgr.load()
        dest = str(tmp_path / "out.json")
        mgr.save(dest)
        with open(dest, "r", encoding="utf-8") as fh:
            reloaded = json.load(fh)
        assert reloaded["version"] == "2.0"
