"""Tests for streaming visualization tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.streaming import create_streaming_plot


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestStreamingPlot:
    def test_basic_streaming(self):
        result = create_streaming_plot(n_points=20)
        assert len(result) == 3
        assert result[0].type == "text"
        assert "streaming" in result[0].text.lower()
        assert result[1].type == "image"
        # HTML should contain Bokeh streaming JS
        html = result[2].resource.text
        assert "bokeh" in html.lower()
        assert "setInterval" in html or "addPoint" in html

    def test_streaming_with_dataset(self):
        load_sample_data("iris")
        result = create_streaming_plot(dataset_name="iris", y="sepal_length", n_points=30)
        assert len(result) == 3
        assert result[1].type == "image"

    def test_streaming_scatter(self):
        result = create_streaming_plot(plot_type="scatter", n_points=15)
        assert len(result) == 3
        html = result[2].resource.text
        assert "scatter" in html

    def test_streaming_area(self):
        result = create_streaming_plot(plot_type="area", n_points=15)
        assert len(result) == 3

    def test_streaming_step(self):
        result = create_streaming_plot(plot_type="step", n_points=15)
        assert len(result) == 3

    def test_custom_title(self):
        result = create_streaming_plot(title="My Live Feed")
        html = result[2].resource.text
        assert "My Live Feed" in html

    def test_custom_interval(self):
        result = create_streaming_plot(update_interval=1000)
        html = result[2].resource.text
        assert "1000" in html
