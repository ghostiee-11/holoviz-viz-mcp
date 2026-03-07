"""Statistical testing tools: t-test, correlation, regression with visualizations.

Bridges the gap between visualization and rigorous statistics — no competitor
MCP offers real p-values, confidence intervals, or regression diagnostics.
"""

from __future__ import annotations

import base64
from typing import Any

import holoviews as hv
import hvplot.pandas  # noqa: F401
import numpy as np
import pandas as pd
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

from ..rendering import render_to_html, render_to_png
from ..state import state


def statistical_test(
    dataset_name: str,
    test_type: str,
    column_x: str,
    column_y: str | None = None,
    group_column: str | None = None,
    confidence: float = 0.95,
) -> list:
    """Run a statistical test and return results with a diagnostic plot.

    Supports t-test, correlation, regression, chi-square, and normality tests.
    Returns both numerical results (p-values, effect sizes) and a visualization.

    Args:
        dataset_name: Name of the loaded dataset
        test_type: Test to run — 'ttest', 'correlation', 'regression', 'chi2', 'normality', 'anova'
        column_x: Primary column (numeric for most tests)
        column_y: Second column (for correlation/regression) or value column (for ttest)
        group_column: Grouping column for t-test/ANOVA (splits data into groups)
        confidence: Confidence level (default 0.95)
    """
    from scipy import stats as sp_stats

    df = state.get_dataset(dataset_name)
    results: list[str] = [f"# Statistical Test: {test_type.upper()}"]
    plot_obj = None

    if test_type == "ttest":
        if not group_column:
            return [TextContent(type="text", text="Error: t-test requires 'group_column' to split data into two groups.")]
        groups = df[group_column].unique()
        if len(groups) < 2:
            return [TextContent(type="text", text=f"Error: '{group_column}' has only {len(groups)} group(s). Need at least 2.")]

        g1 = df[df[group_column] == groups[0]][column_x].dropna()
        g2 = df[df[group_column] == groups[1]][column_x].dropna()

        t_stat, p_value = sp_stats.ttest_ind(g1, g2)
        effect_size = abs(g1.mean() - g2.mean()) / np.sqrt((g1.std() ** 2 + g2.std() ** 2) / 2)

        results.append(f"**Groups:** '{groups[0]}' (n={len(g1)}) vs '{groups[1]}' (n={len(g2)})")
        results.append(f"**Variable:** {column_x}")
        results.append(f"**t-statistic:** {t_stat:.4f}")
        results.append(f"**p-value:** {p_value:.6f}")
        results.append(f"**Effect size (Cohen's d):** {effect_size:.4f}")
        results.append(f"**Significant at {confidence:.0%}?** {'Yes' if p_value < (1 - confidence) else 'No'}")
        results.append(f"\n**Group means:** {groups[0]}={g1.mean():.4f}, {groups[1]}={g2.mean():.4f}")

        # Box plot comparing groups
        subset = df[df[group_column].isin(groups[:2])]
        plot_obj = subset.hvplot.box(
            y=column_x, by=group_column,
            title=f"T-Test: {column_x} by {group_column} (p={p_value:.4f})",
            width=500, height=400, color="#4a90d9",
        )

    elif test_type == "correlation":
        if not column_y:
            return [TextContent(type="text", text="Error: correlation requires 'column_y'.")]

        x = df[column_x].dropna()
        y = df[column_y].dropna()
        common = df[[column_x, column_y]].dropna()

        pearson_r, pearson_p = sp_stats.pearsonr(common[column_x], common[column_y])
        spearman_r, spearman_p = sp_stats.spearmanr(common[column_x], common[column_y])

        results.append(f"**Variables:** {column_x} vs {column_y} (n={len(common)})")
        results.append(f"**Pearson r:** {pearson_r:.4f} (p={pearson_p:.6f})")
        results.append(f"**Spearman rho:** {spearman_r:.4f} (p={spearman_p:.6f})")
        results.append(f"**R-squared:** {pearson_r**2:.4f}")

        strength = "strong" if abs(pearson_r) > 0.7 else "moderate" if abs(pearson_r) > 0.4 else "weak"
        direction = "positive" if pearson_r > 0 else "negative"
        results.append(f"**Interpretation:** {strength} {direction} correlation")

        # Scatter with regression line
        slope, intercept = np.polyfit(common[column_x], common[column_y], 1)
        line_x = np.linspace(common[column_x].min(), common[column_x].max(), 100)
        line_y = slope * line_x + intercept

        scatter = common.hvplot.scatter(
            x=column_x, y=column_y,
            title=f"Correlation: r={pearson_r:.3f}, p={pearson_p:.4f}",
            width=500, height=400, alpha=0.6,
        )
        reg_line = hv.Curve(
            pd.DataFrame({"x": line_x, "y": line_y}), "x", "y"
        ).opts(color="red", line_dash="dashed", line_width=2)
        plot_obj = scatter * reg_line

    elif test_type == "regression":
        if not column_y:
            return [TextContent(type="text", text="Error: regression requires 'column_y' (dependent variable).")]

        common = df[[column_x, column_y]].dropna()
        slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
            common[column_x], common[column_y]
        )

        results.append(f"**Model:** {column_y} = {slope:.4f} * {column_x} + {intercept:.4f}")
        results.append(f"**R-squared:** {r_value**2:.4f}")
        results.append(f"**p-value (slope):** {p_value:.6f}")
        results.append(f"**Standard error:** {std_err:.4f}")
        results.append(f"**Slope interpretation:** For each unit increase in {column_x}, {column_y} changes by {slope:.4f}")

        # Residuals
        predicted = slope * common[column_x] + intercept
        residuals = common[column_y] - predicted
        results.append(f"**Residual std:** {residuals.std():.4f}")

        # Scatter + regression line + residuals
        line_x = np.linspace(common[column_x].min(), common[column_x].max(), 100)
        line_y = slope * line_x + intercept

        scatter = common.hvplot.scatter(
            x=column_x, y=column_y,
            title=f"Regression: R²={r_value**2:.3f}, p={p_value:.4f}",
            width=500, height=400, alpha=0.6,
        )
        reg_line = hv.Curve(
            pd.DataFrame({"x": line_x, "y": line_y}), "x", "y"
        ).opts(color="red", line_width=2)

        # Confidence interval band
        alpha = 1 - confidence
        ci = sp_stats.t.ppf(1 - alpha / 2, len(common) - 2) * std_err
        upper = line_y + ci * np.sqrt(1 + 1 / len(common))
        lower = line_y - ci * np.sqrt(1 + 1 / len(common))
        ci_area = hv.Area(
            pd.DataFrame({"x": line_x, "upper": upper, "lower": lower}),
            "x", ["upper", "lower"],
        ).opts(alpha=0.15, color="red")

        plot_obj = ci_area * scatter * reg_line

    elif test_type == "chi2":
        if not column_y:
            return [TextContent(type="text", text="Error: chi-square test requires 'column_y' (second categorical column).")]

        contingency = pd.crosstab(df[column_x], df[column_y])
        chi2, p_value, dof, expected = sp_stats.chi2_contingency(contingency)

        results.append(f"**Variables:** {column_x} vs {column_y}")
        results.append(f"**Chi-square statistic:** {chi2:.4f}")
        results.append(f"**p-value:** {p_value:.6f}")
        results.append(f"**Degrees of freedom:** {dof}")
        n = contingency.values.sum()
        cramers_v = np.sqrt(chi2 / (n * (min(contingency.shape) - 1)))
        results.append(f"**Cramer's V (effect size):** {cramers_v:.4f}")
        results.append(f"**Significant at {confidence:.0%}?** {'Yes' if p_value < (1 - confidence) else 'No'}")

        # Heatmap of observed counts
        records = []
        for i, idx in enumerate(contingency.index):
            for j, col in enumerate(contingency.columns):
                records.append({"x": str(col), "y": str(idx), "count": int(contingency.iloc[i, j])})
        hm_df = pd.DataFrame(records)
        plot_obj = hm_df.hvplot.heatmap(
            x="x", y="y", C="count",
            title=f"Chi-Square: p={p_value:.4f}",
            cmap="YlOrRd", width=500, height=400,
        )

    elif test_type == "normality":
        data = df[column_x].dropna()

        # Shapiro-Wilk (up to 5000 samples)
        sample = data if len(data) <= 5000 else data.sample(5000, random_state=42)
        shapiro_stat, shapiro_p = sp_stats.shapiro(sample)

        # D'Agostino-Pearson (needs n >= 20)
        if len(data) >= 20:
            dagostino_stat, dagostino_p = sp_stats.normaltest(data)
        else:
            dagostino_stat, dagostino_p = float("nan"), float("nan")

        results.append(f"**Variable:** {column_x} (n={len(data)})")
        results.append(f"**Shapiro-Wilk:** W={shapiro_stat:.4f}, p={shapiro_p:.6f}")
        if not np.isnan(dagostino_p):
            results.append(f"**D'Agostino-Pearson:** stat={dagostino_stat:.4f}, p={dagostino_p:.6f}")
        results.append(f"**Skewness:** {data.skew():.4f}")
        results.append(f"**Kurtosis:** {data.kurtosis():.4f}")
        is_normal = shapiro_p > (1 - confidence)
        results.append(f"**Normal at {confidence:.0%}?** {'Yes (fail to reject H0)' if is_normal else 'No (reject H0)'}")

        # Histogram with normal overlay
        hist = data.hvplot.hist(
            bins=30, title=f"Normality: {column_x} (Shapiro p={shapiro_p:.4f})",
            width=500, height=400, color="#4a90d9", density=True,
        )
        x_range = np.linspace(data.min(), data.max(), 200)
        normal_curve = sp_stats.norm.pdf(x_range, data.mean(), data.std())
        curve = hv.Curve(
            pd.DataFrame({"x": x_range, "density": normal_curve}), "x", "density"
        ).opts(color="red", line_width=2, line_dash="dashed")
        plot_obj = hist * curve

    elif test_type == "anova":
        if not group_column:
            return [TextContent(type="text", text="Error: ANOVA requires 'group_column' to split data into groups.")]

        groups_data = []
        group_names = df[group_column].unique()
        for g in group_names:
            groups_data.append(df[df[group_column] == g][column_x].dropna().values)

        f_stat, p_value = sp_stats.f_oneway(*groups_data)

        results.append(f"**Variable:** {column_x} across {len(group_names)} groups of {group_column}")
        results.append(f"**F-statistic:** {f_stat:.4f}")
        results.append(f"**p-value:** {p_value:.6f}")
        results.append(f"**Significant at {confidence:.0%}?** {'Yes' if p_value < (1 - confidence) else 'No'}")

        for g, gd in zip(group_names, groups_data):
            results.append(f"  - {g}: mean={np.mean(gd):.4f}, std={np.std(gd):.4f}, n={len(gd)}")

        # Box plot
        plot_obj = df.hvplot.box(
            y=column_x, by=group_column,
            title=f"ANOVA: F={f_stat:.2f}, p={p_value:.4f}",
            width=500, height=400,
        )

    else:
        return [TextContent(type="text", text=f"Unknown test '{test_type}'. Use: ttest, correlation, regression, chi2, normality, anova.")]

    # Build output
    narrative = "\n".join(results)

    if plot_obj is None:
        return [TextContent(type="text", text=narrative)]

    plot_id = state.save_plot(plot_obj, {"type": "statistical_test", "test": test_type}, dataset_name)
    png_bytes = render_to_png(plot_obj)
    html = render_to_html(plot_obj)

    return [
        TextContent(type="text", text=f"Statistical test '{test_type}' complete.\n\n{narrative}"),
        ImageContent(type="image", data=base64.b64encode(png_bytes).decode(), mimeType="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(
                uri=f"viz://stats/{test_type}_{dataset_name}",
                mimeType="text/html",
                text=html,
            ),
        ),
    ]
