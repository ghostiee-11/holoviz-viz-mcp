"""Tests for state management module."""

import pandas as pd
import pytest

from holoviz_viz_mcp.state import StateManager


@pytest.fixture
def sm():
    return StateManager()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [10, 20, 30, 40, 50],
        "cat": ["a", "b", "a", "b", "a"],
    })


class TestDatasets:
    def test_store_and_get(self, sm, sample_df):
        data_id = sm.store_dataset(sample_df, "test")
        assert data_id == "test"
        result = sm.get_dataset("test")
        pd.testing.assert_frame_equal(result, sample_df)

    def test_auto_name(self, sm, sample_df):
        data_id = sm.store_dataset(sample_df)
        assert data_id.startswith("data_")
        assert sm.get_dataset(data_id) is not None

    def test_get_missing_raises(self, sm):
        with pytest.raises(KeyError, match="not found"):
            sm.get_dataset("nonexistent")

    def test_list_datasets(self, sm, sample_df):
        sm.store_dataset(sample_df, "ds1")
        result = sm.list_datasets()
        assert "ds1" in result
        rows, cols, columns = result["ds1"]
        assert rows == 5
        assert cols == 3
        assert "x" in columns


class TestPlots:
    def test_save_and_get(self, sm):
        obj = "mock_plot_object"
        pid = sm.save_plot(obj, {"type": "scatter"}, "ds1")
        assert pid.startswith("plot_")
        version = sm.get_plot(pid)
        assert version["obj"] == "mock_plot_object"
        assert version["spec"] == {"type": "scatter"}

    def test_versioning(self, sm):
        pid = sm.save_plot("v1", {"type": "scatter"}, "ds1", plot_id="p1")
        sm.save_plot("v2", {"type": "scatter"}, "ds1", plot_id="p1")
        latest = sm.get_plot("p1")
        assert latest["obj"] == "v2"

    def test_undo(self, sm):
        sm.save_plot("v1", {"type": "scatter"}, "ds1", plot_id="p1")
        sm.save_plot("v2", {"type": "scatter"}, "ds1", plot_id="p1")
        reverted = sm.undo_plot("p1")
        assert reverted["obj"] == "v1"

    def test_undo_at_first_version_raises(self, sm):
        sm.save_plot("v1", {"type": "scatter"}, "ds1", plot_id="p1")
        with pytest.raises(ValueError, match="Nothing to undo"):
            sm.undo_plot("p1")

    def test_get_missing_raises(self, sm):
        with pytest.raises(KeyError, match="not found"):
            sm.get_plot("nonexistent")

    def test_list_plots(self, sm):
        sm.save_plot("v1", {"plot_type": "scatter", "x": "a", "y": "b"}, "ds1", plot_id="p1")
        result = sm.list_plots()
        assert "p1" in result
        assert result["p1"]["spec"]["plot_type"] == "scatter"
        assert result["p1"]["n_versions"] == 1
