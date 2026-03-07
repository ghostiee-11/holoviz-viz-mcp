"""Tests for export tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot
from holoviz_viz_mcp.tools.export import export_plot


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


@pytest.fixture
def plot_id():
    load_sample_data("iris")
    result = create_plot("iris", "scatter", x="sepal_length", y="sepal_width")
    return result[0].text.split("'")[1]


class TestExportPlot:
    def test_export_html(self, plot_id):
        result = export_plot(plot_id, format="html")
        assert len(result) == 2
        assert "HTML" in result[0].text
        assert "bokeh" in result[1].text.lower()

    def test_export_png(self, plot_id):
        result = export_plot(plot_id, format="png")
        assert len(result) == 2
        assert "PNG" in result[0].text
        # base64 data should be non-empty
        assert len(result[1].text) > 100

    def test_export_unknown_format(self, plot_id):
        result = export_plot(plot_id, format="gif")
        assert "Unknown format" in result[0].text

    def test_export_custom_size(self, plot_id):
        result = export_plot(plot_id, format="html", width=400, height=300)
        assert "HTML" in result[0].text
