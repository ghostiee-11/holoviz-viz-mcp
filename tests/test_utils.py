"""Tests for utility tools: describe, clone, sample, session."""

import json
import os
import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.viz import create_plot
from holoviz_viz_mcp.tools.utils import (
    describe_plot, clone_plot, get_data_sample, save_session, load_session,
)


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


class TestDescribePlot:
    def test_describe(self, scatter_plot):
        result = describe_plot(scatter_plot)
        assert "scatter" in result
        assert "sepal_length" in result
        assert "sepal_width" in result

    def test_describe_data_range(self, scatter_plot):
        result = describe_plot(scatter_plot)
        assert "X range" in result or "Y range" in result

    def test_describe_color(self, scatter_plot):
        result = describe_plot(scatter_plot)
        assert "species" in result


class TestClonePlot:
    def test_clone(self, scatter_plot):
        result = clone_plot(scatter_plot)
        assert "Cloned" in result
        plots = global_state.list_plots()
        assert len(plots) == 2

    def test_clone_with_title(self, scatter_plot):
        result = clone_plot(scatter_plot, new_title="My Clone")
        assert "Cloned" in result


class TestGetDataSample:
    def test_sample(self):
        load_sample_data("iris")
        result = get_data_sample("iris")
        assert "5 of 150" in result
        assert "sepal_length" in result

    def test_sample_n(self):
        load_sample_data("iris")
        result = get_data_sample("iris", n_rows=3)
        assert "3 of 150" in result

    def test_sample_columns(self):
        load_sample_data("iris")
        result = get_data_sample("iris", columns="sepal_length,species")
        assert "sepal_length" in result

    def test_sample_random(self):
        load_sample_data("iris")
        result = get_data_sample("iris", random=True)
        assert "5 of 150" in result


class TestSessionPersistence:
    def test_save_and_load(self, tmp_path):
        load_sample_data("iris")
        path = str(tmp_path / "test_session.json")

        save_result = save_session(path)
        assert "1 dataset(s)" in save_result

        # Clear state
        global_state.datasets.clear()
        assert len(global_state.datasets) == 0

        # Load back
        load_result = load_session(path)
        assert "1 dataset(s) restored" in load_result
        assert "iris" in global_state.datasets

    def test_save_multiple(self, tmp_path):
        load_sample_data("iris")
        load_sample_data("tips")
        path = str(tmp_path / "multi_session.json")

        save_result = save_session(path)
        assert "2 dataset(s)" in save_result
