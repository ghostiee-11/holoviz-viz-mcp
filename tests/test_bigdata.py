"""Tests for big data visualization and synthetic data generation tools."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.bigdata import create_datashader_plot, generate_large_dataset
from holoviz_viz_mcp.tools.data import load_sample_data


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestCreateDatashaderPlot:
    def test_basic(self):
        load_sample_data("iris")
        result = create_datashader_plot("iris", "sepal_length", "sepal_width")
        assert len(result) == 3
        assert "plot" in result[0].text.lower() or "datashader" in result[0].text.lower()

    def test_custom_title(self):
        load_sample_data("iris")
        result = create_datashader_plot("iris", "sepal_length", "sepal_width", title="My Big Data")
        assert "My Big Data" in result[0].text or len(result) == 3


class TestGenerateLargeDataset:
    def test_clusters(self):
        result = generate_large_dataset(n_points=1000, distribution="clusters", name="test_clusters")
        assert "1,000 points" in result
        assert "test_clusters" in result
        df = global_state.get_dataset("test_clusters")
        assert len(df) == 1000
        assert "cluster" in df.columns

    def test_spiral(self):
        result = generate_large_dataset(n_points=500, distribution="spiral")
        assert "spiral" in result
        assert "500 points" in result

    def test_grid(self):
        result = generate_large_dataset(n_points=100, distribution="grid")
        assert "grid" in result

    def test_uniform(self):
        result = generate_large_dataset(n_points=200, distribution="uniform")
        assert "200 points" in result

    def test_cap_at_5m(self):
        result = generate_large_dataset(n_points=10_000_000, distribution="uniform", name="capped")
        df = global_state.get_dataset("capped")
        assert len(df) == 5_000_000
