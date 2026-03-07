"""Tests for the statistical_test tool."""

import pytest

from holoviz_viz_mcp.state import state as global_state
from holoviz_viz_mcp.tools.data import load_sample_data
from holoviz_viz_mcp.tools.statistics import statistical_test


@pytest.fixture(autouse=True)
def clean_state():
    global_state.datasets.clear()
    global_state.plots.clear()
    yield
    global_state.datasets.clear()
    global_state.plots.clear()


@pytest.fixture
def iris_data():
    load_sample_data("iris")


class TestStatisticalTest:
    def test_ttest(self, iris_data):
        result = statistical_test("iris", "ttest", "sepal_length", group_column="species")
        text = result[0].text
        assert "t-statistic" in text
        assert "p-value" in text
        assert "Cohen's d" in text
        assert len(result) == 3  # text + image + resource

    def test_ttest_no_group(self, iris_data):
        result = statistical_test("iris", "ttest", "sepal_length")
        assert "Error" in result[0].text

    def test_correlation(self, iris_data):
        result = statistical_test("iris", "correlation", "sepal_length", column_y="petal_length")
        text = result[0].text
        assert "Pearson" in text
        assert "Spearman" in text
        assert "R-squared" in text

    def test_correlation_no_y(self, iris_data):
        result = statistical_test("iris", "correlation", "sepal_length")
        assert "Error" in result[0].text

    def test_regression(self, iris_data):
        result = statistical_test("iris", "regression", "petal_length", column_y="petal_width")
        text = result[0].text
        assert "R-squared" in text
        assert "Slope interpretation" in text

    def test_chi2(self, iris_data):
        import pandas as pd
        df = pd.DataFrame({
            "color": ["red"] * 30 + ["blue"] * 25 + ["red"] * 20 + ["blue"] * 25,
            "shape": ["circle"] * 55 + ["square"] * 45,
        })
        global_state.store_dataset(df, "chi2_test")
        result = statistical_test("chi2_test", "chi2", "color", column_y="shape")
        text = result[0].text
        assert "Chi-square" in text
        assert "Cramer" in text

    def test_normality(self, iris_data):
        result = statistical_test("iris", "normality", "sepal_length")
        text = result[0].text
        assert "Shapiro" in text
        assert "Skewness" in text

    def test_anova(self, iris_data):
        result = statistical_test("iris", "anova", "sepal_length", group_column="species")
        text = result[0].text
        assert "F-statistic" in text
        assert "p-value" in text

    def test_unknown_test(self, iris_data):
        result = statistical_test("iris", "kruskal", "sepal_length")
        assert "Unknown" in result[0].text
