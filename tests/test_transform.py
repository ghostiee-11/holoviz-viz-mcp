"""Tests for data transformation tools."""

import pandas as pd
import pytest

from holoviz_viz_mcp.state import StateManager, state as global_state
from holoviz_viz_mcp.tools.transform import merge_datasets, transform_data


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


@pytest.fixture
def sample_data():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6],
        "y": [10, 20, 30, 40, 50, 60],
        "cat": ["A", "B", "A", "B", "A", "B"],
        "val": [1.1, 2.2, 3.3, 4.4, 5.5, 6.6],
    })
    global_state.store_dataset(df, "test")
    return df


class TestTransformData:
    def test_filter(self, sample_data):
        result = transform_data("test", "filter", column="x", value="> 3")
        assert "test_filter" in result
        assert "3 rows" in result

    def test_filter_missing_params(self, sample_data):
        result = transform_data("test", "filter")
        assert "Error" in result

    def test_groupby(self, sample_data):
        result = transform_data("test", "groupby", group_by="cat", agg="sum")
        assert "test_groupby" in result
        assert "2 rows" in result

    def test_groupby_missing_param(self, sample_data):
        result = transform_data("test", "groupby")
        assert "Error" in result

    def test_sort(self, sample_data):
        result = transform_data("test", "sort", sort_by="y", ascending=False)
        assert "test_sort" in result

    def test_sort_missing_param(self, sample_data):
        result = transform_data("test", "sort")
        assert "Error" in result

    def test_derive(self, sample_data):
        result = transform_data("test", "derive", expression="x * y", new_column="product")
        assert "product" in result
        assert "test_derive" in result

    def test_derive_missing_param(self, sample_data):
        result = transform_data("test", "derive", expression="x + 1")
        assert "Error" in result

    def test_sample(self, sample_data):
        result = transform_data("test", "sample", limit=3)
        assert "3 rows" in result

    def test_drop_na(self):
        df = pd.DataFrame({"a": [1, 2, None, 4], "b": [None, 2, 3, 4]})
        global_state.store_dataset(df, "nulls")
        result = transform_data("nulls", "drop_na")
        assert "dropped" in result
        assert "2 rows remaining" in result

    def test_drop_na_column(self):
        df = pd.DataFrame({"a": [1, 2, None, 4], "b": [None, 2, 3, 4]})
        global_state.store_dataset(df, "nulls")
        result = transform_data("nulls", "drop_na", column="a")
        assert "dropped 1" in result

    def test_custom_output_name(self, sample_data):
        result = transform_data("test", "sample", output_name="my_sample", limit=2)
        assert "my_sample" in result
        assert "my_sample" in global_state.datasets

    def test_limit(self, sample_data):
        result = transform_data("test", "filter", column="x", value="> 0", limit=2)
        assert "2 rows" in result

    def test_unknown_operation(self, sample_data):
        result = transform_data("test", "foobar")
        assert "Unknown operation" in result


class TestMergeDatasets:
    def test_merge(self):
        left = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        right = pd.DataFrame({"id": [2, 3, 4], "label": ["a", "b", "c"]})
        global_state.store_dataset(left, "left")
        global_state.store_dataset(right, "right")
        result = merge_datasets("left", "right", on="id")
        assert "2 rows" in result
        assert "merged" in result

    def test_merge_outer(self):
        left = pd.DataFrame({"id": [1, 2], "v": [10, 20]})
        right = pd.DataFrame({"id": [2, 3], "w": [30, 40]})
        global_state.store_dataset(left, "l")
        global_state.store_dataset(right, "r")
        result = merge_datasets("l", "r", on="id", how="outer")
        assert "3 rows" in result

    def test_merge_custom_name(self):
        left = pd.DataFrame({"id": [1], "v": [10]})
        right = pd.DataFrame({"id": [1], "w": [20]})
        global_state.store_dataset(left, "a")
        global_state.store_dataset(right, "b")
        result = merge_datasets("a", "b", on="id", output_name="combined")
        assert "combined" in result
