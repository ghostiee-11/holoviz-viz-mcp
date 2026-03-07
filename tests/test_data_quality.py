"""Tests for data_quality_report and compare_datasets tools."""

import pytest
import numpy as np
import pandas as pd

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.data_quality import data_quality_report, compare_datasets


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestDataQualityReport:
    def test_clean_dataset(self):
        load_sample_data("iris")
        result = data_quality_report("iris")
        text = result[0].text
        assert "Quality Score" in text
        assert "No missing values" in text or "complete" in text.lower()

    def test_dataset_with_missing(self):
        df = pd.DataFrame({
            "a": [1, 2, np.nan, 4, 5, np.nan, 7, 8],
            "b": [np.nan, 2, 3, np.nan, 5, 6, np.nan, 8],
            "c": ["x", "y", "x", "y", "x", "y", "x", "y"],
        })
        global_state.store_dataset(df, "messy")
        result = data_quality_report("messy")
        text = result[0].text
        assert "Missing Values" in text
        assert "completeness" in text.lower()

    def test_outlier_detection_iqr(self):
        df = pd.DataFrame({
            "normal": np.random.normal(0, 1, 100).tolist() + [100.0],
            "cat": ["a"] * 101,
        })
        global_state.store_dataset(df, "outlier_test")
        result = data_quality_report("outlier_test", outlier_method="iqr")
        text = result[0].text
        assert "Outlier" in text or "outlier" in text

    def test_outlier_detection_zscore(self):
        df = pd.DataFrame({
            "normal": np.random.normal(0, 1, 100).tolist() + [100.0],
        })
        global_state.store_dataset(df, "outlier_z")
        result = data_quality_report("outlier_z", outlier_method="zscore")
        text = result[0].text
        assert "Outlier" in text or "outlier" in text

    def test_duplicate_detection(self):
        df = pd.DataFrame({
            "a": [1, 1, 2, 3],
            "b": ["x", "x", "y", "z"],
        })
        global_state.store_dataset(df, "dupes")
        result = data_quality_report("dupes")
        text = result[0].text
        assert "Duplicate" in text or "duplicate" in text

    def test_quality_score(self):
        load_sample_data("iris")
        result = data_quality_report("iris")
        text = result[0].text
        assert "/100" in text


class TestCompareDatasets:
    def test_compare_same(self):
        load_sample_data("iris")
        result = compare_datasets("iris", "iris")
        assert "150" in result  # Same shape
        assert "Common columns: 5" in result

    def test_compare_different(self):
        load_sample_data("iris")
        load_sample_data("tips")
        result = compare_datasets("iris", "tips")
        assert "iris" in result
        assert "tips" in result

    def test_compare_overlapping_columns(self):
        df1 = pd.DataFrame({"a": [1, 2], "b": [3, 4], "c": [5, 6]})
        df2 = pd.DataFrame({"a": [7, 8], "b": [9, 10], "d": [11, 12]})
        global_state.store_dataset(df1, "left")
        global_state.store_dataset(df2, "right")
        result = compare_datasets("left", "right")
        assert "Common columns: 2" in result
        assert "Only in left" in result
        assert "Only in right" in result
