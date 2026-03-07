"""Tests for annotation and overlay tools."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot
from holoviz_viz_mcp.tools.annotations import annotate_plot, overlay_plots


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


@pytest.fixture
def scatter_plot():
    load_sample_data("iris")
    result = create_plot("iris", "scatter", x="sepal_length", y="sepal_width")
    plot_id = result[0].text.split("'")[1]
    return plot_id


class TestAnnotatePlot:
    def test_hline(self, scatter_plot):
        result = annotate_plot(scatter_plot, "hline", value=3.0)
        assert len(result) == 3
        assert result[0].type == "text"
        assert "hline" in result[0].text

    def test_vline(self, scatter_plot):
        result = annotate_plot(scatter_plot, "vline", value=5.5)
        assert len(result) == 3
        assert "vline" in result[0].text

    def test_hline_missing_value(self, scatter_plot):
        result = annotate_plot(scatter_plot, "hline")
        assert "Error" in result[0].text

    def test_vline_missing_value(self, scatter_plot):
        result = annotate_plot(scatter_plot, "vline")
        assert "Error" in result[0].text

    def test_text_annotation(self, scatter_plot):
        result = annotate_plot(scatter_plot, "text", x=5.0, y=3.5, label="Outlier")
        assert len(result) == 3
        assert "Outlier" in result[0].text

    def test_text_missing_params(self, scatter_plot):
        result = annotate_plot(scatter_plot, "text", x=5.0)
        assert "Error" in result[0].text

    def test_point_annotation(self, scatter_plot):
        result = annotate_plot(scatter_plot, "point", x=5.0, y=3.5)
        assert len(result) == 3
        assert "point" in result[0].text

    def test_point_missing_params(self, scatter_plot):
        result = annotate_plot(scatter_plot, "point", x=5.0)
        assert "Error" in result[0].text

    def test_unknown_type(self, scatter_plot):
        result = annotate_plot(scatter_plot, "zigzag")
        assert "Unknown" in result[0].text

    def test_arrow(self, scatter_plot):
        result = annotate_plot(scatter_plot, "arrow", x=5.0, y=3.0, label="Look here")
        assert len(result) == 3
        assert "arrow" in result[0].text

    def test_hspan(self, scatter_plot):
        result = annotate_plot(scatter_plot, "hspan", y_start=2.5, y_end=3.5)
        assert len(result) == 3
        assert "hspan" in result[0].text

    def test_vspan(self, scatter_plot):
        result = annotate_plot(scatter_plot, "vspan", x_start=5.0, x_end=6.0)
        assert len(result) == 3
        assert "vspan" in result[0].text

    def test_hspan_missing_params(self, scatter_plot):
        result = annotate_plot(scatter_plot, "hspan", y_start=2.5)
        assert "Error" in result[0].text

    def test_vspan_missing_params(self, scatter_plot):
        result = annotate_plot(scatter_plot, "vspan", x_start=5.0)
        assert "Error" in result[0].text


class TestOverlayPlots:
    def test_overlay_two_plots(self):
        load_sample_data("iris")
        r1 = create_plot("iris", "scatter", x="sepal_length", y="sepal_width")
        r2 = create_plot("iris", "scatter", x="sepal_length", y="petal_width")
        id1 = r1[0].text.split("'")[1]
        id2 = r2[0].text.split("'")[1]
        result = overlay_plots(f"{id1},{id2}", title="Comparison")
        assert len(result) == 3
        assert "overlay" in result[0].text.lower() or "Comparison" in result[0].text

    def test_overlay_too_few(self):
        load_sample_data("iris")
        r1 = create_plot("iris", "scatter", x="sepal_length", y="sepal_width")
        id1 = r1[0].text.split("'")[1]
        result = overlay_plots(id1)
        assert "Error" in result[0].text
