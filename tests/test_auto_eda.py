"""Tests for the auto_eda tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.auto_eda import auto_eda


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestAutoEDA:
    def test_iris_eda(self):
        load_sample_data("iris")
        result = auto_eda("iris")
        assert len(result) == 3  # text + image + resource
        text = result[0].text
        assert "Auto-EDA" in text
        assert "150" in text  # 150 rows
        assert "Numeric columns" in text

    def test_eda_with_correlations(self):
        load_sample_data("iris")
        result = auto_eda("iris", include_correlations=True)
        text = result[0].text
        assert "correlation" in text.lower()

    def test_eda_without_correlations(self):
        load_sample_data("iris")
        result = auto_eda("iris", include_correlations=False)
        assert len(result) >= 1

    def test_eda_missing_data(self):
        import pandas as pd
        import numpy as np
        df = pd.DataFrame({
            "a": [1, 2, np.nan, 4, 5],
            "b": [np.nan, 2, 3, np.nan, 5],
            "c": ["x", "y", "x", "y", "x"],
        })
        global_state.store_dataset(df, "missing_test")
        result = auto_eda("missing_test")
        text = result[0].text
        assert "Missing" in text or "missing" in text

    def test_eda_max_plots(self):
        load_sample_data("iris")
        result = auto_eda("iris", max_plots=2)
        assert len(result) >= 1

    def test_eda_categorical(self):
        load_sample_data("tips")
        result = auto_eda("tips")
        text = result[0].text
        assert "244" in text or "Categorical" in text.lower() or "mode" in text.lower()

    def test_eda_returns_plot_id(self):
        load_sample_data("iris")
        result = auto_eda("iris")
        # Should have saved a plot in state
        plots = global_state.list_plots()
        assert len(plots) >= 1
