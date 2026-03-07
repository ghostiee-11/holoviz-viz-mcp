"""Tests for time series analysis tools."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.timeseries import time_series_analysis


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


@pytest.fixture
def stock_data():
    load_sample_data("stocks")


@pytest.fixture
def weather_data():
    load_sample_data("weather")


class TestTimeSeriesAnalysis:
    def test_overview(self, stock_data):
        result = time_series_analysis("stocks", "date", "price", analysis="overview")
        assert len(result) == 3
        text = result[0].text
        assert "Mean" in text
        assert "trend" in text.lower()

    def test_decomposition(self, weather_data):
        result = time_series_analysis("weather", "date", "temperature", analysis="decomposition")
        assert len(result) == 3
        text = result[0].text
        assert "Trend" in text
        assert "Seasonal" in text or "Residual" in text

    def test_change_detection(self, stock_data):
        result = time_series_analysis("stocks", "date", "price", analysis="change_detection")
        assert len(result) >= 1
        text = result[0].text
        assert "Anomal" in text or "anomal" in text

    def test_comparison(self, stock_data):
        result = time_series_analysis(
            "stocks", "date", "price",
            analysis="comparison", group_by="company"
        )
        assert len(result) == 3
        text = result[0].text
        assert "Groups" in text

    def test_custom_window(self, weather_data):
        result = time_series_analysis(
            "weather", "date", "temperature",
            analysis="overview", window=30
        )
        assert len(result) == 3
        assert "Mean" in result[0].text

    def test_unknown_analysis(self, stock_data):
        result = time_series_analysis("stocks", "date", "price", analysis="wavelet")
        assert "Unknown" in result[0].text
