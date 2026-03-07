"""Tests for MCP tool functions."""

import asyncio

import pytest
from mcp.types import EmbeddedResource, ImageContent, TextContent

from holoviz_viz_mcp.state import StateManager, state as global_state
from holoviz_viz_mcp.tools.data import (
    analyze_data,
    list_datasets,
    load_data,
    load_sample_data,
    suggest_visualizations,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Reset global state before each test."""
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


CSV_DATA = """x,y,category
1,10,A
2,20,B
3,30,A
4,40,B
5,50,A"""


class TestDataTools:
    def test_load_data(self):
        result = load_data(CSV_DATA, name="test")
        assert "Loaded dataset 'test'" in result
        assert "5 rows x 3 columns" in result
        assert "x" in result

    def test_load_data_auto_name(self):
        result = load_data(CSV_DATA)
        assert "Loaded dataset" in result

    def test_list_datasets_empty(self):
        result = list_datasets()
        assert "No datasets loaded" in result

    def test_list_datasets_with_data(self):
        load_data(CSV_DATA, name="mydata")
        result = list_datasets()
        assert "mydata" in result
        assert "5 rows" in result

    def test_analyze_data(self):
        load_data(CSV_DATA, name="test")
        result = analyze_data("test")
        assert "Data Profile: test" in result
        assert "Numeric Columns" in result

    def test_analyze_missing_dataset(self):
        with pytest.raises(KeyError):
            analyze_data("nonexistent")

    def test_suggest_visualizations(self):
        load_data(CSV_DATA, name="test")
        result = suggest_visualizations("test")
        assert "Scatter" in result or "Bar chart" in result

    def test_load_sample_iris(self):
        result = load_sample_data("iris")
        assert "iris" in result
        assert "sepal_length" in result

    def test_load_sample_tips(self):
        result = load_sample_data("tips")
        assert "tips" in result
        assert "total_bill" in result

    def test_load_sample_stocks(self):
        result = load_sample_data("stocks")
        assert "stocks" in result
        assert "company" in result

    def test_load_sample_unknown(self):
        result = load_sample_data("nonexistent")
        assert "Unknown dataset" in result


class TestVizToolsMCP:
    """Test visualization tools through the MCP server call_tool interface."""

    def test_create_plot_returns_triple(self):
        """create_plot should return TextContent + ImageContent + EmbeddedResource."""
        from holoviz_viz_mcp.server import mcp

        load_sample_data("iris")
        result = asyncio.run(mcp.call_tool("create_plot", {
            "dataset_name": "iris",
            "plot_type": "scatter",
            "x": "sepal_length",
            "y": "sepal_width",
        }))
        content = result.content
        assert len(content) == 3
        assert content[0].type == "text"
        assert content[1].type == "image"
        assert content[2].type == "resource"
        # HTML should contain Bokeh script
        assert "bokeh" in content[2].resource.text.lower()

    def test_execute_code(self):
        """execute_code should run arbitrary hvPlot code and return visualization."""
        from holoviz_viz_mcp.server import mcp

        load_sample_data("iris")
        result = asyncio.run(mcp.call_tool("execute_code", {
            "code": "result = df.hvplot.scatter('sepal_length', 'sepal_width')",
            "dataset_name": "iris",
        }))
        content = result.content
        assert len(content) == 3
        assert "custom_code" in content[0].text or "Custom" in content[0].text

    def test_execute_code_no_result(self):
        """execute_code without result variable should return text warning."""
        from holoviz_viz_mcp.server import mcp

        result = asyncio.run(mcp.call_tool("execute_code", {
            "code": "x = 42",
        }))
        content = result.content
        assert any("no `result`" in c.text for c in content if hasattr(c, "text"))
