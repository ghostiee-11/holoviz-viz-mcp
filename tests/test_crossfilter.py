"""Tests for crossfilter linked brushing tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.crossfilter import create_crossfilter


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestCrossfilter:
    def test_basic_crossfilter(self):
        load_sample_data("iris")
        result = create_crossfilter(
            "iris",
            views="scatter,sepal_length,sepal_width;hist,petal_length",
        )
        assert len(result) == 3
        assert "crossfilter" in result[0].text.lower()
        assert "2 linked views" in result[0].text
        assert result[1].type == "image"
        assert "bokeh" in result[2].resource.text.lower()

    def test_crossfilter_with_color(self):
        load_sample_data("iris")
        result = create_crossfilter(
            "iris",
            views="scatter,sepal_length,sepal_width;box,species,petal_length",
            color_by="species",
        )
        assert len(result) == 3
        assert "2 linked views" in result[0].text

    def test_crossfilter_three_views(self):
        load_sample_data("iris")
        result = create_crossfilter(
            "iris",
            views="scatter,sepal_length,sepal_width;hist,petal_length;hist,petal_width",
        )
        assert "3 linked views" in result[0].text

    def test_crossfilter_empty_views(self):
        load_sample_data("iris")
        result = create_crossfilter("iris", views="")
        assert "Error" in result[0].text or "no valid" in result[0].text.lower()

    def test_crossfilter_custom_title(self):
        load_sample_data("iris")
        result = create_crossfilter(
            "iris",
            views="scatter,sepal_length,sepal_width",
            title="My Crossfilter",
        )
        assert len(result) == 3
