"""Tests for interactive tools: handle_click, set_theme, launch_panel."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot
from holoviz_viz_mcp.tools.interact import handle_click, set_theme, stop_panel


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
    result = create_plot("iris", "scatter", x="sepal_length", y="sepal_width", color_by="species")
    return result[0].text.split("'")[1]


class TestHandleClick:
    def test_click_with_point_index(self, scatter_plot):
        result = handle_click(scatter_plot, x_value=5.1, y_value=3.5, point_index=0)
        assert "Click Insight" in result
        assert "Full data row" in result

    def test_click_with_x_value_nearest(self, scatter_plot):
        result = handle_click(scatter_plot, x_value=5.1)
        assert "Click Insight" in result
        assert "Nearest data row" in result or "Statistical context" in result

    def test_click_with_statistics(self, scatter_plot):
        result = handle_click(scatter_plot, x_value=5.1, y_value=3.5, point_index=0)
        assert "percentile" in result

    def test_click_group_context(self, scatter_plot):
        result = handle_click(scatter_plot, x_value=5.1, point_index=0)
        assert "Group context" in result or "species" in result

    def test_click_outlier_detection(self, scatter_plot):
        # Use extreme value
        result = handle_click(scatter_plot, x_value=99.0, y_value=99.0, point_index=0)
        assert "Click Insight" in result

    def test_click_no_dataset(self):
        global_state.save_plot("obj", {"type": "test"}, "nonexistent", plot_id="test1")
        result = handle_click("test1", x_value=1.0)
        assert "No source dataset" in result

    def test_click_invalid_index(self, scatter_plot):
        result = handle_click(scatter_plot, x_value=5.0, point_index=99999)
        assert "Click Insight" in result


class TestSetTheme:
    def test_set_default(self):
        result = set_theme("default")
        assert "default" in result

    def test_set_dark(self):
        result = set_theme("dark")
        assert "dark" in result

    def test_set_midnight(self):
        result = set_theme("midnight")
        assert "midnight" in result

    def test_invalid_theme(self):
        result = set_theme("neon")
        assert "Unknown" in result


class TestStopPanel:
    def test_no_servers(self):
        result = stop_panel()
        assert "No Panel servers" in result
