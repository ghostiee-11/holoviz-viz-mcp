"""Tests for the natural_language_query tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.nlq import natural_language_query


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


class TestNaturalLanguageQuery:
    def test_distribution_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "show the distribution of sepal_length")
        assert "hist" in result
        assert "sepal_length" in result

    def test_comparison_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "compare sepal_length by species")
        assert "groupby" in result or "bar" in result

    def test_correlation_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "is there a correlation between sepal_length and petal_length")
        assert "correlation" in result or "statistical_test" in result

    def test_top_n_intent(self):
        load_sample_data("tips")
        result = natural_language_query("tips", "show top 5 by total_bill")
        assert "sort" in result or "top" in result.lower()
        assert "5" in result

    def test_trend_intent(self):
        load_sample_data("stocks")
        result = natural_language_query("stocks", "show price trend over time")
        assert "line" in result

    def test_summary_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "give me an overview of this data")
        assert "auto_eda" in result or "analyze" in result

    def test_quality_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "check data quality and missing values")
        assert "quality" in result or "data_quality" in result

    def test_filter_detection(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "show scatter where sepal_length > 5")
        assert "filter" in result or "sepal_length" in result

    def test_unknown_intent(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "xyzzy")
        assert "auto_eda" in result or "analyze" in result

    def test_query_plan_header(self):
        load_sample_data("iris")
        result = natural_language_query("iris", "show distribution of petal_width")
        assert "Query Plan" in result
        assert "iris" in result
