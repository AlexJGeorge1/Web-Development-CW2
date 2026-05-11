"""
Tests for the storage module: save and load with error handling.
"""

import json
import os
import pytest

from storage import save_index, load_index


@pytest.fixture
def sample_index():
    """A small index for testing save/load."""
    return {
        "hello": {
            "http://example.com": {
                "frequency": 2,
                "positions": [0, 5]
            }
        },
        "world": {
            "http://example.com": {
                "frequency": 1,
                "positions": [1]
            }
        }
    }


@pytest.fixture
def index_path(tmp_path):
    """Provide a temporary file path for the index."""
    return str(tmp_path / "test_index.json")


class TestSaveIndex:
    """Tests for save_index."""

    def test_save_creates_file(self, sample_index, index_path):
        """Saving should create the JSON file on disk."""
        save_index(sample_index, index_path)
        assert os.path.exists(index_path)

    def test_saved_file_is_valid_json(self, sample_index, index_path):
        """The saved file should contain valid JSON."""
        save_index(sample_index, index_path)
        with open(index_path, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_save_creates_directories(self, sample_index, tmp_path):
        """Saving to a nested path should create parent directories."""
        nested_path = str(tmp_path / "a" / "b" / "index.json")
        save_index(sample_index, nested_path)
        assert os.path.exists(nested_path)

    def test_save_empty_index(self, index_path):
        """Saving an empty index should work without errors."""
        save_index({}, index_path)
        with open(index_path, "r") as f:
            data = json.load(f)
        assert data == {}


class TestLoadIndex:
    """Tests for load_index."""

    def test_load_returns_same_data(self, sample_index, index_path):
        """Loading a saved index should return the same data."""
        save_index(sample_index, index_path)
        loaded = load_index(index_path)
        assert loaded == sample_index

    def test_load_preserves_structure(self, sample_index, index_path):
        """The loaded index should have the same nested structure."""
        save_index(sample_index, index_path)
        loaded = load_index(index_path)
        assert loaded["hello"]["http://example.com"]["frequency"] == 2
        assert loaded["hello"]["http://example.com"]["positions"] == [0, 5]

    def test_load_missing_file_raises(self):
        """Loading a non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_index("/nonexistent/path/index.json")

    def test_load_invalid_json_raises(self, tmp_path):
        """Loading a file with invalid JSON should raise JSONDecodeError."""
        bad_file = str(tmp_path / "bad.json")
        with open(bad_file, "w") as f:
            f.write("this is not json {{{")

        with pytest.raises(json.JSONDecodeError):
            load_index(bad_file)

    def test_roundtrip_empty_index(self, index_path):
        """An empty index should survive a save/load round-trip."""
        save_index({}, index_path)
        loaded = load_index(index_path)
        assert loaded == {}
